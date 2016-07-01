use strict;
use warnings;
our (%access);
our $module_name;

do 'virtualmin-init-lib.pl';

sub cgi_args
{
my ($cgi) = @_;
my ($d) = grep { &virtual_server::can_edit_domain($_) &&
	         $_->{$module_name} } &virtual_server::list_domains();
if ($cgi eq 'edit.cgi') {
	return $d ? 'dom='.$d->{'id'}.'&new=1' : 'none';
	}
elsif ($cgi eq 'edit_tmpl.cgi') {
	my @tmpls = &list_action_templates();
	return !$access{'templates'} ? 'none' :
	       @tmpls ? 'id='.$tmpls[0]->{'id'} : 'new=1';
	}
return undef;
}
