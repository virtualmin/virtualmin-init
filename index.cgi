#!/usr/local/bin/perl
# Show a list of bootup scripts that the user already has configured
use strict;
use warnings;
our (%access, %text, %in);
our $module_name;

require './virtualmin-init-lib.pl';
&ReadParse();
my $d = $in{'dom'} ? &virtual_server::get_domain($in{'dom'}) : undef;
&ui_print_header($d ? &virtual_server::domain_in($d) : undef,
		 $text{'index_title'}, "", undef, 0, 1);
my @templates = &list_action_templates();

# Work out domains to work on
my @doms;
my $many;

if ($d) {
	# Just one
	@doms = ( $d );
	}
else {
	# All domains for the user
	@doms = grep { $_->{$module_name} &&
		       &virtual_server::can_edit_domain($_) }
		     &virtual_server::list_domains();
	$many = 1;
	}

# Show existing init scripts for all domains
my @allinits;
foreach my $d (@doms) {
	foreach my $i (&list_domain_actions($d)) {
		$i->{'dom'} = $d->{'id'};
		$i->{'domname'} = $d->{'dom'};
		push(@allinits, $i);
		}
	}

# Work out limit
my $no_create;
if ($access{'max'}) {
	my $c = &count_user_actions();
	if ($c >= $access{'max'}) {
		print "<b>",&text('index_hitmax', $access{'max'}),"</b><p>\n";
		$no_create = 1;
		}
	elsif ($c) {
		print "<b>",&text('index_max', $c, $access{'max'}),"</b><p>\n";
		}
	else {
		print "<b>",&text('index_max2', $access{'max'}),"</b><p>\n";
		}
	}

# Build contents for table of actions
my @links;
if (!$no_create) {
	push(@links, [ "edit.cgi?new=1&dom=".&urlize($in{'dom'}),
		       $text{'index_add'} ]);
	foreach my $tmpl (@templates) {
		push(@links, [ "edit.cgi?new=1&dom=".&urlize($in{'dom'}).
			       "&tmpl=$tmpl->{'id'}",
			       &text('index_add2', $tmpl->{'desc'}) ]);
		}
	}
my $green = "<font color=#00aa00>$text{'yes'}</font>";
my $red = "<font color=#ff0000>$text{'no'}</font>";
my $orange = "<font color=#ffaa00>$text{'index_maint'}</font>";
my @table;
foreach my $i (sort { $a->{'name'} cmp $b->{'name'} } @allinits) {
	push(@table, [
		{ 'type' => 'checkbox', 'name' => 'd',
		  'value' => $i->{'dom'}."/".$i->{'name'} },
		"<a href='edit.cgi?id=".&urlize($i->{'id'}).
		 "&dom=$i->{'dom'}'>$i->{'name'}</a>",
		$many ? ( $i->{'domname'} ) : ( ),
		$i->{'desc'},
		$i->{'status'} == 1 ? $green :
		$i->{'status'} == 2 ? $orange :
				      $red
		]);
	}

# Render the table of actions
print &ui_form_columns_table(
	"mass.cgi",
	[ [ "delete", $text{'index_delete'} ],
	  undef,
	  [ "startnow", $text{'index_startnow'} ],
	  [ "stopnow", $text{'index_stopnow'} ],
	  [ "restartnow", $text{'index_restartnow'} ] ],
	1,
	\@links,
	undef,
	[ "", $text{'index_name'},
	  $many ? ( $text{'index_dom'} ) : ( ),
	  $text{'index_desc'},
	  &can_start_actions() ? $text{'index_status'} : $text{'index_status2'}
	],
	100,
	\@table,
	undef,
	0,
	undef,
	$in{'dom'} ? $text{'index_none'} : $text{'index_none2'}
	);


# Show list of templates
if ($access{'templates'}) {
	print &ui_hr();
	print $text{'index_tdesc2'},"<p>\n";
	@table = ( );
	foreach my $t (@templates) {
		push(@table, [
			"<a href='edit_tmpl.cgi?id=$t->{'id'}'>".
			"$t->{'desc'}</a>",
			&shorten_command($t->{'start'}),
			&shorten_command($t->{'stop'}),
			]);
		}
	print &ui_form_columns_table(
		undef,
		undef,
		0,
		[ [ "edit_tmpl.cgi?new=1", $text{'index_tadd'} ] ],
		undef,
		[ $text{'index_tdesc'}, $text{'index_tstart'},
		  $text{'index_tstop'} ],
		100,
		\@table,
		undef, 0, undef, $text{'index_tnone'});
	}

&ui_print_footer("/", $text{'index'});

sub shorten_command
{
my ($cmd) = @_;
if ($cmd eq ":kill") {
	return $text{'index_kill'};
	}
$cmd =~ s/\n/ ; /g;
if (length($cmd) > 60) {
	$cmd = substr($cmd, 0, 60)." ...";
	}
return &html_escape($cmd);
}
