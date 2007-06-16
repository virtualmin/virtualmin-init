# Functions for domain-level init scripts
# XXX cd to home directory
# XXX malicious use of VIRTUALMINEOF, or ` within su block

do '../web-lib.pl';
&init_config();
do '../ui-lib.pl';
&foreign_require("virtual-server", "virtual-server-lib.pl");
%access = &get_module_acl();

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
					'name' => $2 };
			$init->{'status'} = &init::action_status($a) == 2;
			local $data = &read_file_contents(
					&init::action_filename($a));
			($init->{'start'}, $init->{'user'}) =
				&extract_action_command('start', $data);
			($init->{'stop'}) =
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

# extract_action_command(section, script)
sub extract_action_command
{
local ($section, $data) = @_;
if ($data =~ /'\Q$section\E')\n([\000-\377]*?);;/) {
	# Found the section .. get out the su command
	local $script = $1;
	$script =~ s/\s+$//;
	if ($script =~ /^\s*su\s+\-\s+(\S+)\s*<<VIRTUALMINEOF\ncd\s*(.*)\n([\000-\377]*)VIRTUALMINEOF/) {
		return ($1, $3, $2);
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
	return "su - $init->{'user'} <<VIRTUALMINEOF\n".
	       "cd $dir\n".
	       $init->{$section}."\n".
	       "VIRTUALMINEOF\n";
	}
else {
	return undef;
	}
}

1;

