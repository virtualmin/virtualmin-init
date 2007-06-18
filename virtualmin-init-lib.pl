# Functions for domain-level init scripts
# XXX SMF

do '../web-lib.pl';
&init_config();
do '../ui-lib.pl';
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
	# XXX smf check
	}
return undef;
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
					'name' => $1 };
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
	# Use SMF
	# XXX
	}
return @rv;
}

# create_domain_action(&domain, &action)
# Creates the init script or SMF service for some new action
sub create_domain_action
{
local ($d, $init) = @_;
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
	# Add SMF
	# XXX
	}
}

# modify_domain_action(&domain, &olddomain, &action, &oldaction)
# Modifies the init script or SMF service for some action
sub modify_domain_action
{
local ($d, $oldd, $init, $oldinit) = @_;
if ($config{'mode'} eq 'init') {
	# Just delete old init script and re-create
	&foreign_require("init", "init-lib.pl");
	&delete_domain_action($oldd, $oldinit);
	&create_domain_action($d, $init);
	}
else {
	# What to do for SMF?
	# XXX
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
	# XXX
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
	# Run SMF action
	# XXX
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
	# Run SMF action
	# XXX
	}
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
&make_dir($action_templates_dir, 0700);
&write_file("$action_templates_dir/$tmpl->{'id'}", \%savetmpl);
}

# delete_action_template(&tmpl)
sub delete_action_template
{
local ($tmpl) = @_;
unlink("$action_templates_dir/$tmpl->{'id'}");
}

1;

