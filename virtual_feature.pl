# Defines functions for this feature
use strict;
use warnings;
our (%text);
our $module_name;

do 'virtualmin-init-lib.pl';
my $input_name = $module_name;
$input_name =~ s/[^A-Za-z0-9]/_/g;

# feature_name()
# Returns a short name for this feature
sub feature_name
{
return $text{'feat_name'};
}

# feature_losing(&domain)
# Returns a description of what will be deleted when this feature is removed
sub feature_losing
{
return $text{'feat_losing'};
}

# feature_label(in-edit-form)
# Returns the name of this feature, as displayed on the domain creation and
# editing form
sub feature_label
{
my ($edit) = @_;
return $edit ? $text{'feat_label2'} : $text{'feat_label'};
}

# feature_hlink(in-edit-form)
# Returns a help page linked to by the label returned by feature_label
sub feature_hlink
{
return 'label';
}

# feature_check()
# Returns undef if all the needed programs for this feature are installed,
# or an error message if not
sub feature_check
{
return &virtualmin_init_check();
}

# feature_depends(&domain)
# Returns undef if all pre-requisite features for this domain are enabled,
# or an error message if not
sub feature_depends
{
return !$_[0]->{'unix'} && !$_[0]->{'parent'} ? $text{'feat_eunix'} :
			  undef;
}

# feature_clash(&domain)
# Returns undef if there is no clash for this domain for this feature, or
# an error message if so
sub feature_clash
{
return undef;	# Can never clash
}

# feature_suitable([&parentdom], [&aliasdom], [&subdom])
# Returns 1 if some feature can be used with the specified alias,
# parent and sub domains
sub feature_suitable
{
return !$_[1] && !$_[2];
}

# feature_setup(&domain)
# Called when this feature is added, with the domain object as a parameter
sub feature_setup
{
# Does nothing, as no setup is needed
}

# feature_modify(&domain, &olddomain)
# Called when a domain with this feature is modified, to rename scripts if
# user or domain is changed
sub feature_modify
{
my ($d, $oldd) = @_;
if ($d->{'dom'} ne $oldd->{'dom'} ||
    $d->{'user'} ne $oldd->{'user'}) {
	# Need to re-save all actions under the new user or domain name
	&$virtual_server::first_print($text{'feat_rename'});
	my $c = 0;
	foreach my $init (&list_domain_actions($oldd)) {
		my $oldinit = { %$init };
		$init->{'user'} = $d->{'user'};
		&modify_domain_action($d, $oldd, $init, $oldinit);
		$c++;
		}
	if ($c) {
		&$virtual_server::second_print(
			$virtual_server::text{'setup_done'});
		}
	else {
		&$virtual_server::second_print($text{'feat_norename'});
		}
	}
}

# feature_delete(&domain)
# Called when this feature is disabled, or when the domain is being deleted.
# Removes all bootup scripts for the domain.
sub feature_delete
{
my ($d) = @_;
&$virtual_server::first_print($text{'feat_delete'});
my $c = 0;
foreach my $init (&list_domain_actions($d)) {
	&delete_domain_action($d, $init);
	$c++;
	}
if ($c) {
	&$virtual_server::second_print(
		$virtual_server::text{'setup_done'});
	}
else {
	&$virtual_server::second_print($text{'feat_norename'});
	}
}

# feature_webmin(&main-domain, &all-domains)
# Returns a list of webmin module names and ACL hash references to be set for
# the Webmin user when this feature is enabled
# (optional)
sub feature_webmin
{
my ($d, $doms) = @_;
my @doms = &unique(map { $_->{'id'} } grep { $_->{$module_name} } @$doms);
if (@doms) {
	return ( [ $module_name,
		   { 'doms' => join(' ', @doms),
		     'max' => $d->{$module_name.'limit'},
		     'templates' => 0 } ] );
	}
else {
	return ( );
	}
}

# feature_limits_input(&domain)
# Returns HTML for editing limits related to this plugin
sub feature_limits_input
{
my ($d) = @_;
return undef if (!$d->{$module_name});
return &ui_table_row(&hlink($text{'limits_max'}, "limits_max"),
	&ui_opt_textbox($input_name."limit", $d->{$module_name."limit"},
			4, $virtual_server::text{'form_unlimit'},
			   $virtual_server::text{'form_atmost'}));
}

# feature_limits_parse(&domain, &in)
# Updates the domain with limit inputs generated by feature_limits_input
sub feature_limits_parse
{
my ($d, $in) = @_;
return undef if (!$d->{$module_name});
if ($in->{$input_name."limit_def"}) {
	delete($d->{$module_name."limit"});
	}
else {
	$in->{$input_name."limit"} =~ /^\d+$/ || return $text{'limit_emax'};
	$d->{$module_name."limit"} = $in->{$input_name."limit"};
	}
return undef;
}

# feature_links(&domain)
# Returns an array of link objects for webmin modules for this feature
sub feature_links
{
my ($d) = @_;
return ( { 'mod' => $module_name,
	   'desc' => $text{'links_link'},
	   'page' => 'index.cgi?dom='.$d->{'id'},
	   'cat' => 'services',
	 } );
}

sub feature_modules
{
return ( [ $module_name, $text{'feat_module'} ] );
}

# feature_backup(&domain, file, &opts, &all-opts)
# Called to backup this feature for the domain to the given file. Must return 1
# on success or 0 on failure.
# Gets all action objects for the domain, and serializes them to the file.
sub feature_backup
{
my ($d, $file) = @_;
&$virtual_server::first_print($text{'feat_backup'});
my $actions = [ &list_domain_actions($d) ];
no strict "subs";
&virtual_server::open_tempfile_as_domain_user($d, INIT, ">$file") || return 0;
&print_tempfile(INIT, &serialise_variable($actions));
&virtual_server::close_tempfile_as_domain_user($d, INIT);
use strict "subs";
if (@$actions) {
	&$virtual_server::second_print($virtual_server::text{'setup_done'});
	}
else {
	&$virtual_server::second_print($text{'feat_norename'});
	}
return 1;
}

# feature_restore(&domain, file, &opts, &all-opts)
# Called to restore this feature for the domain from the given file. Must
# return 1 on success or 0 on failure.
# Reads the serialized actions from the file, deletes existing actions, then
# re-creates them.
sub feature_restore
{
my ($d, $file) = @_;
my $data = &read_file_contents($file);
if ($data) {
	&$virtual_server::first_print($text{'feat_restore'});
	my $actions = &unserialise_variable($data);
	foreach my $init (&list_domain_actions($d)) {
		&delete_domain_action($d, $init);
		}
	foreach my $init (@$actions) {
		&create_domain_action($d, $init);
		}
	&$virtual_server::second_print($virtual_server::text{'setup_done'});
	}
return 1;
}

# feature_backup_name()
# Returns a description for what is backed up for this feature
sub feature_backup_name
{
return $text{'feat_bname'};
}

1;
