# Functions for domain-level init scripts

BEGIN { push(@INC, ".."); };
eval "use WebminCore;";
&init_config();
&foreign_require("virtual-server", "virtual-server-lib.pl");
%access = &get_module_acl();
$action_templates_dir = "$module_config_directory/templates";

# virtualmin_init_check()
# Returns an error if some required config is missing
sub virtualmin_init_check
{
if ($config{'mode'} eq 'init') {
	&foreign_check("init") || return $text{'check_einit'};
	&foreign_require("init", "init-lib.pl");
	$init::init_mode eq "init" || return $text{'check_einit2'};
	}
else {
	foreach my $c ("svcs", "svccfg", "svcadm") {
		&has_command($c) || return &text('check_esmf', "<tt>$c</tt>");
		}
	}
return undef;
}

# Returns 1 if actions can be started separately from their boot status
sub can_start_actions
{
return $config{'mode'} eq 'init';
}

# list_domain_actions(&domain)
# Returns a list of init scripts belonging to the specified domain. These
# are determined from the script prefix.
sub list_domain_actions
{
local ($d) = @_;
local @rv;
if ($config{'mode'} eq 'init') {
	# Use init scripts
	&foreign_require("init", "init-lib.pl");
	foreach my $a (&init::list_actions()) {
		$a =~ s/\s+\d+$//;
		if ($a =~ /^\Q$d->{'dom'}\E_(\S+)$/) {
			# Found one for the domain
			local $init = { 'type' => 'init',
					'name' => $1,
					'id' => $1 };
			$init->{'desc'} = &init::init_description(
					    &init::action_filename($a), { });
			$init->{'status'} = &init::action_status($a) == 2;
			local $data = &read_file_contents(
					&init::action_filename($a));
			($init->{'user'}, $init->{'start'}) =
				&extract_action_command('start', $data);
			(undef, $init->{'stop'}) =
				&extract_action_command('stop', $data);
			push(@rv, $init);
			}
		}
	}
else {
	# Use SMF. First find virtualmin services, then get their details
	open(SVCS, "svcs -a |");
	while(<SVCS>) {
		s/\r|\n//g;
		local ($state, $when, $fmri) = split(/\s+/, $_);
		local $usdom = &make_fmri_domain($d->{'dom'});
		if ($fmri =~ /^svc:\/virtualmin\/\Q$usdom\E\/(.+):default$/ ||
		    $fmri =~ /^svc:\/virtualmin\/[^\/]+\/\Q$usdom\E\/([^:]+):([^:]+)/) {
			# Found one for the domain .. get the commands
			# and user
			local $init = { 'type' => 'smf',
					'name' => $2 && $2 ne "default" ? $2 : $1,
					'fmri' => $fmri,
					'id' => $fmri,
					'status' =>
						$state eq 'online' ? 1 :
						$state eq 'maintenance' ? 2 : 0,
					'smfstate' => $state };
			$init->{'desc'} = &get_smf_prop($fmri,
							"tm_common_name/C");
			$init->{'user'} = &get_smf_prop($fmri, "start/user");
			$init->{'start'} = &get_smf_prop($fmri, "start/exec");
			$init->{'start'} = join("\n",
						split(/;/, $init->{'start'}));
			$init->{'stop'} = &get_smf_prop($fmri, "stop/exec");
			$init->{'stop'} = join("\n",
					       split(/;/, $init->{'stop'}));
			$init->{'startlog'} = &get_smf_log_tail($init);
			push(@rv, $init);
			}
		}
	close(SVCS);
	}
return @rv;
}

# create_domain_action(&domain, &action, [&template, &template-params])
# Creates the init script or SMF service for some new action
sub create_domain_action
{
local ($d, $init, $tmpl, $tparams) = @_;
if ($config{'mode'} eq 'init') {
	# Add init script
	&foreign_require("init", "init-lib.pl");
	local $start = &make_action_command('start', $init, $d->{'home'});
	local $stop = &make_action_command('stop', $init, $d->{'home'});
	&init::enable_at_boot($d->{'dom'}."_".$init->{'name'},
			      $init->{'desc'}, $start, $stop);
	local $if = &init::action_filename($d->{'dom'}."_".$init->{'name'});
	local $data = &read_file_contents($if);
	$data =~ s/[ \t]+(VIRTUALMINEOF)/$1/g;	# Remove tab at start
	&open_tempfile(INIT, ">$if");
	&print_tempfile(INIT, $data);
	&close_tempfile(INIT);
	if (!$init->{'status'}) {
		&init::disable_at_boot($d->{'dom'}."_".$init->{'name'});
		}
	}
else {
	# Add SMF, by taking XML template and subbing it
	local $xml = $tmpl->{'xml'} ||
		     &read_file_contents(
			$config{'xml'} ||
			"$module_root_directory/template.xml");
	local $usdom = &make_fmri_domain($d->{'dom'});
	local %hash = ( 'DOM' => $usdom,
			'DESC' => $init->{'desc'},
			'NAME' => $init->{'name'},
			'START' => join(';', split(/\n/, $init->{'start'})),
			'STOP' => join(';', split(/\n/, $init->{'stop'})),
			'USER' => $d->{'user'},
			'GROUP' => $d->{'group'},
			'HOME' => $d->{'home'} );
	%hash = ( %hash, %$tparams );
	$hash{'START'} =~ s/\n*$//g;
	$hash{'STOP'} =~ s/\n*$//g;
	$xml = &substitute_template($xml, \%hash);
	local $temp = &transname();
	&open_tempfile(TEMP, ">$temp", 0, 1);
	&print_tempfile(TEMP, $xml);
	&close_tempfile(TEMP);
	local $out = `svccfg -v import $temp 2>&1`;
	if ($? || $out =~ /failed/) {
		&error("<pre>".&html_escape($out)."</pre>");
		}
	# Work out FMRI
	if ($out =~ /Refreshed\s+(svc:.*)\./) {
		$init->{'fmri'} = $1;
		}
	else {
		$init->{'fmri'} = "svc:/virtualmin/$usdom/$init->{'name'}";
		}
	&execute_command("svcadm refresh $init->{'fmri'}");
	if (!$init->{'status'}) {
		# Make sure disabled after creation
		&execute_command(
			"svcadm disable $init->{'fmri'}");
		}
	}
}

# modify_domain_action(&domain, &olddomain, &action, &oldaction)
# Modifies the init script or SMF service for some action
sub modify_domain_action
{
local ($d, $oldd, $init, $oldinit) = @_;
if ($config{'mode'} eq 'init') {
	# Just delete old init script and re-create
	&delete_domain_action($oldd, $oldinit);
	&create_domain_action($d, $init);
	}
else {
	# For SMF, if the domain or service name has changed, then the
	# FMRI may have too ... so we need to export the XML, patch it,
	# delete the service, then re-create.
	local $stopped;
	if ($d->{'dom'} ne $oldd->{'dom'} ||
	    $d->{'user'} ne $oldd->{'user'} ||
	    $init->{'name'} ne $oldinit->{'name'}) {
		# Export XML
		local $fmri = $oldinit->{'fmri'};
		$fmri =~ s/:[^:\/]+$//;
		local $xml = `svccfg export $fmri`;
		if ($?) {
			&error("SMF XML export failed : $xml");
			}

		# Shut down under the old name, if it was running
		if ($init->{'status'} == 1) {
			&capture_function_output(
				\&stop_domain_action, $oldd, $init);
			$stopped = 1;
			}

		# Replace service name, domain name and user
		if ($d->{'dom'} ne $oldd->{'dom'}) {
			local $usdom = &make_fmri_domain($d->{'dom'});
			local $oldusdom = &make_fmri_domain($oldd->{'dom'});
			$xml =~ s/\Q$oldusdom\E/$usdom/g;
			}
		if ($d->{'user'} ne $oldd->{'user'}) {
			local $user = $d->{'user'};
			local $olduser = $oldd->{'user'};
			$xml =~ s/\/\Q$olduser\E\//\/$user\//g;
			}
		if ($init->{'name'} ne $oldinit->{'name'}) {
			local $name = $init->{'name'};
			local $oldname = $oldinit->{'name'};
			$xml =~ s/\/\Q$oldname\E'/\/$name'/g;
			$xml =~ s/'\Q$oldname\E'/'$name'/g;
			}

		# Delete and re-import
		local $out = `svccfg delete -f $init->{'fmri'} 2>&1`;
		local $temp = &transname();
		&open_tempfile(TEMP, ">$temp", 0, 1);
		&print_tempfile(TEMP, $xml);
		&close_tempfile(TEMP);
		local $out = `svccfg -v import $temp 2>&1`;
		if ($? || $out =~ /failed/) {
			&error("SMF XML import failed : $out");
			}
		if ($out =~ /Refreshed\s+(svc:.*)\./) {
			$init->{'fmri'} = $1;
			}
		&execute_command("svcadm refresh $init->{'fmri'}");

		# Start under the new name
		if ($stopped) {
			&capture_function_output(
				\&start_domain_action, $d, $init);
			}
		}

	# Update start and stop commands
	&set_smf_prop($init->{'fmri'}, "start/exec",
		join(';', split(/\n/, $init->{'start'})), "astring");
	&set_smf_prop($init->{'fmri'}, "stop/exec",
		join(';', split(/\n/, $init->{'stop'})), "astring");

	# Update description
	&set_smf_prop($init->{'fmri'}, "tm_common_name/C",
		$init->{'desc'}, "ustring");

	# Update user
	&set_smf_prop($init->{'fmri'}, "start/user",
		$d->{'user'}, "astring");
	&set_smf_prop($init->{'fmri'}, "start/group",
		$d->{'group'}, "astring");
	&set_smf_prop($init->{'fmri'}, "stop/user",
		$d->{'user'}, "astring");
	&set_smf_prop($init->{'fmri'}, "stop/group",
		$d->{'group'}, "astring");

	&execute_command("svcadm refresh $init->{'fmri'}");

	if ($init->{'status'} == 1 && $oldinit->{'status'} == 0) {
		# Enable service
		local $out = `svcadm enable $init->{'fmri'} 2>&1`;
		$? && &error("<pre>".&html_escape($out)."</pre>");
		}
	elsif ($init->{'status'} == 0 && $oldinit->{'status'} == 1) {
		# Disable service
		local $out = `svcadm disable $init->{'fmri'} 2>&1`;
		$? && &error("<pre>".&html_escape($out)."</pre>");
		}
	elsif ($init->{'status'} == 1 && $oldinit->{'status'} == 2) {
		# Clear and enable
		local $out = `svcadm clear $init->{'fmri'} && svcadm enable $init->{'fmri'} 2>&1`;
		$? && &error("<pre>".&html_escape($out)."</pre>");
		}
	elsif ($init->{'status'} == 0 && $oldinit->{'status'} == 2) {
		# Just clear
		local $out = `svcadm clear $init->{'fmri'} 2>&1`;
		$? && &error("<pre>".&html_escape($out)."</pre>");
		}
	}
}

# delete_domain_action(&domain, &action)
# Deletes the init script or SMF service for some action
sub delete_domain_action
{
local ($d, $init) = @_;
if ($config{'mode'} eq 'init') {
	# Delete init script and links
	&foreign_require("init", "init-lib.pl");
	local $name = $d->{'dom'}.'_'.$init->{'name'};
	foreach my $l (&init::action_levels('S', $name)) {
		$l =~ /^(\S+)\s+(\S+)\s+(\S+)$/;
		&init::delete_rl_action($name, $1, 'S');
		}
	foreach my $l (&init::action_levels('K', $name)) {
		$l =~ /^(\S+)\s+(\S+)\s+(\S+)$/;
		&init::delete_rl_action($name, $1, 'K');
		}
	unlink(&init::action_filename($name));
	}
else {
	# Delete SMF service
	&execute_command("svcadm disable $init->{'fmri'}");
	sleep(2);	# Wait for disable
	local $out = `svccfg delete -f $init->{'fmri'} 2>&1`;
	&error("<pre>".&html_escape($out)."</pre>") if ($? || $out =~ /failed/);

	# If there are no more services with the same base fmri (ie. without the
	# :whatever suffix), delete the base too
	if ($init->{'fmri'} =~ /^(.*):([^:]+)$/) {
		local $basefmri = $1;
		local @others = &list_domain_actions($d);
		@others = grep { $_->{'fmri'} =~ /^\Q$basefmi\E:/ } @others;
		if (!@others) {
			$out = `svccfg delete -f $basefmri 2>&1`;
			}
		}
	}
}

# start_domain_action(&domain, &init)
# Start some init script, and output the results
sub start_domain_action
{
local ($d, $init) = @_;
if ($config{'mode'} eq 'init') {
	# Run init script
	&foreign_require("init", "init-lib.pl");
	local $cmd = &init::action_filename($d->{'dom'}."_".$init->{'name'});
	open(OUT, "$cmd start 2>&1 |");
	while(<OUT>) {
		print &html_escape($_);
		}
	close(OUT);
	}
else {
	# Change status to enabled
	if ($init->{'status'} == 2) {
		# Clear maintenance mode first
		local $out = `svcadm clear $init->{'fmri'} 2>&1`;
		print &html_escape($out);
		}
	local $out = `svcadm enable $init->{'fmri'} 2>&1`;
	print &html_escape($out);
	sleep(5);	# Wait for log
	print &html_escape(&get_smf_log_tail($init));
	}
}

# stop_domain_action(&domain, &init)
# Start some init script, and output the results
sub stop_domain_action
{
local ($d, $init) = @_;
if ($config{'mode'} eq 'init') {
	# Run init script
	&foreign_require("init", "init-lib.pl");
	local $cmd = &init::action_filename($d->{'dom'}."_".$init->{'name'});
	open(OUT, "$cmd stop 2>&1 |");
	while(<OUT>) {
		print &html_escape($_);
		}
	close(OUT);
	}
else {
	# Change status to disabled
	local $out = `svcadm disable $init->{'fmri'} 2>&1`;
	print &html_escape($out);
	sleep(5);	# Wait for log
	print &html_escape(&get_smf_log_tail($init));
	}
}

# restart_domain_action(&domain, &init)
# Stop and then start some init script, and output the results
sub restart_domain_action
{
local ($d, $init) = @_;
if ($config{'mode'} eq 'init') {
	&stop_domain_action($d, $init);
	&start_domain_action($d, $init);
	}
else {
	# Use SMF's restart feature
	local $out = `svcadm restart $init->{'fmri'} 2>&1`;
	print &html_escape($out);
	sleep(5);	# Wait for log
	print &html_escape(&get_smf_log_tail($init));
	}
}

# get_smf_log_tail(&init, [lines])
# Returns the last N (10 by default) lines from an action's SMF log
sub get_smf_log_tail
{
local ($init, $lines) = @_;
$lines ||= 10;
if (!$init->{'startlogfile'}) {
	local $out = `svcs -l $init->{'fmri'}`;
	if ($out =~ /logfile\s+(\S+)/) {
		$init->{'startlogfile'} = $1;
		}
	}
if ($init->{'startlogfile'}) {
	return `tail -$lines $init->{'startlogfile'} 2>/dev/null`;
	}
return undef;
}

# count_user_actions()
# Returns the number of actions the current user has across all domains
sub count_user_actions
{
local @doms = grep { $_->{$module_name} &&
		     &virtual_server::can_edit_domain($_) }
		   &virtual_server::list_domains();
local $c = 0;
foreach my $d (@doms) {
	foreach my $i (&list_domain_actions($d)) {
		$c++;
		}
	}
return $c;
}

# extract_action_command(section, script)
sub extract_action_command
{
local ($section, $data) = @_;
if ($data =~ /'\Q$section\E'\)\n([\000-\377]*?);;/) {
	# Found the section .. get out the su command
	local $script = $1;
	$script =~ s/\s+$//;
	if ($script =~ /^\s*su\s+\-\s+(\S+)\s*<<'VIRTUALMINEOF'\n\s*cd\s*(\S+)\n([\000-\377]*)VIRTUALMINEOF/) {
		local @rv = ($1, $3, $2);
		$rv[1] =~ s/(^|\n)\s*/$1/g;	# strip spaces at start of lines
		return @rv;
		}
	else {
		return ('root', $script);
		}
	}
else {
	return ( );
	}
}

sub make_action_command
{
local ($section, $init, $dir) = @_;
if ($init->{$section}) {
	$init->{$section} =~ /VIRTUALMINEOF/ && &error($text{'save_eeof'});
	return "su - $init->{'user'} <<'VIRTUALMINEOF'\n".
	       "cd $dir\n".
	       $init->{$section}.
	       "VIRTUALMINEOF\n";
	}
else {
	return undef;
	}
}

sub get_smf_prop
{
local ($fmri, $name) = @_;
local $qname = quotemeta($name);
local $qfmri = quotemeta($fmri);
local $out = `svcprop -p $qname $qfmri`;
$out =~ s/\r|\n//g;
if ($out eq '""') {
	# Empty string
	return "";
	}
$out =~ s/\\(.)/$1/g;
return $out;
}

# set_smf_prop(fmri, name, value, type)
sub set_smf_prop
{
local ($fmri, $name, $value, $type) = @_;
if ($fmri =~ /:default$/ || $name eq "tm_common_name/C") {
	$fmri =~ s/:[^\/:]+$//;
	}
if ($type eq "ustring" || $type eq "astring") {
	$value =~ s/\\/\\\\/g;
	$value =~ s/"/\\"/g;
	$value =~ s/'/\\'/g;
	$value = "\"$value\"";
	}
local $qfmri = quotemeta($fmri);
local $qset = quotemeta("setprop $name = $type: $value");
local $out = `svccfg -s $qfmri $qset 2>&1`;
if ($? || $out =~ /failed/) {
	&error("Failed to set SMF property $name to $value : $out");
	}
}

# get_started_processes(&init)
# Returns a list of process IDs and commands started by some action. Only
# works with SMF.
sub get_started_processes
{
local ($init) = @_;
return ( ) if ($config{'mode'} ne 'smf');
&open_execute_command(PROCS, "svcs -p ".quotemeta($init->{'fmri'}), 1);
while(<PROCS>) {
	if (/^\s+\S+\s+(\d+)\s+(\S.*)/) {
		push(@pids, $1);
		}
	}
close(PROCS);
return ( ) if (!@pids);
&foreign_require("proc", "proc-lib.pl");
local %pids = map { $_, 1 } @pids;
return grep { $pids{$_->{'pid'}} } &proc::list_processes();
}

# list_action_templates()
# Returns an array of hash refs, each contain the details of one action template
sub list_action_templates
{
local @rv;
opendir(DIR, $action_templates_dir) || return ( );
foreach my $f (readdir(DIR)) {
	if ($f =~ /^\d+$/) {
		local %tmpl;
		&read_file("$action_templates_dir/$f", \%tmpl);
		$tmpl{'start'} =~ s/\t/\n/g;
		$tmpl{'stop'} =~ s/\t/\n/g;
		$tmpl{'xml'} =~ s/\t/\n/g;
		push(@rv, \%tmpl);
		}
	}
closedir(DIR);
return @rv;
}

# save_action_template(&tmpl)
# Create or update an action template
sub save_action_template
{
local ($tmpl) = @_;
$tmpl->{'id'} ||= time();
local %savetmpl = %$tmpl;
$savetmpl{'start'} =~ s/\n/\t/g;
$savetmpl{'stop'} =~ s/\n/\t/g;
$savetmpl{'xml'} =~ s/\n/\t/g;
&make_dir($action_templates_dir, 0700);
&write_file("$action_templates_dir/$tmpl->{'id'}", \%savetmpl);
}

# delete_action_template(&tmpl)
sub delete_action_template
{
local ($tmpl) = @_;
unlink("$action_templates_dir/$tmpl->{'id'}");
}

# make_fmri_domain(name)
# Removes _ and leading numbers from a domain name
sub make_fmri_domain
{
local ($usdom) = @_;
$usdom =~ s/\./_/g;
$usdom =~ s/^0/zero/g;
$usdom =~ s/^1/one/g;
$usdom =~ s/^2/two/g;
$usdom =~ s/^3/three/g;
$usdom =~ s/^4/four/g;
$usdom =~ s/^5/five/g;
$usdom =~ s/^6/six/g;
$usdom =~ s/^7/seven/g;
$usdom =~ s/^8/eight/g;
$usdom =~ s/^9/nine/g;
return $usdom;
}

# read_opts_file(file)
# Returns an array of option names and values
sub read_opts_file
{
local @rv;
local $file = $_[0];
if ($file !~ /^\// && $file !~ /\|\s*$/) {
	local @uinfo = getpwnam($remote_user);
	if (@uinfo) {
		$file = "$uinfo[7]/$file";
		}
	}
open(FILE, $file);
while(<FILE>) {
	s/\r|\n//g;
	if (/^"([^"]*)"\s+"([^"]*)"$/) {
		push(@rv, [ $1, $2 ]);
		}
	elsif (/^"([^"]*)"$/) {
		push(@rv, [ $1, $1 ]);
		}
	elsif (/^(\S+)\s+(\S.*)/) {
		push(@rv, [ $1, $2 ]);
		}
	else {
		push(@rv, [ $_, $_ ]);
		}
	}
close(FILE);
return @rv;
}

1;

