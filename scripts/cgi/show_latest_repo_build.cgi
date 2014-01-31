#!/usr/bin/perl

# queries jenkins  JSON api to find status of a repo builder
#         buildbot JSON api to find status of a repo builder
#  
#  Call with this parameter:
#  
#  BRANCH          e.g. 2.5.0
#  
use warnings;
#use strict;
$|++;

use File::Basename;
use Cwd qw(abs_path);
BEGIN
    {
    $THIS_DIR = dirname( abs_path($0));    unshift( @INC, $THIS_DIR );
    }
my $installed_URL='http://factory.hq.couchbase.com/cgi/show_latest_repo_build.cgi';

use buildbotQuery   qw(:HTML :JSON );
use buildbotMapping qw(:DEFAULT);
use buildbotReports qw(:DEFAULT);

use jenkinsQuery    qw(:DEFAULT );

use CGI qw(:standard);
my  $query = new CGI;

#my $delay = 2 + int rand(5.3);    sleep $delay;

my ($good_color, $warn_color, $err_color, $note_color) = ('#CCFFDD', '#FFFFCC', '#FFAAAA', '#CCFFFF');

my $timestamp = "";
sub get_timestamp
    {
    my $timestamp;
    my ($second, $minute, $hour, $dayOfMonth, $month, $yearOffset, $dayOfWeek, $dayOfYear, $daylightSavings) = localtime();
    my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
    $month =    1 + $month;
    $year  = 1900 + $yearOffset;
    $timestamp = "page generated $hour:$minute:$second  on $year-$month-$dayOfMonth";
    }

sub print_HTML_Page
    {
    my ($frag_left, $frag_right, $page_title, $color) = @_;
    
    print $query->header;
    print $query->start_html( -title   => $page_title,
                              -BGCOLOR => $color,
                            );
    print "\n".'<div style="overflow-x: hidden">'."\n"
         .'<table border="0" cellpadding="0" cellspacing="0"><tr>'."\n".'<td valign="TOP">'.$frag_left.'</td><td valign="TOP">'.$frag_right.'</td></tr>'."\n".'</table>'
         .'</div>'."\n";
    print $query->end_html;
    }

my $usage = "ERROR: must specify 'branch' param\n\n"
           ."<PRE>"
           ."For example:\n\n"
           ."    $installed_URL?branch=2.5.0\n\n"
           ."</PRE><BR>"
           ."\n\n";

my ($builder, $branch);

if ( $query->param('branch') )
    {
    $branch  = $query->param('branch');
    $builder = buildbotMapping::get_repo_builder( $branch );
    print STDERR "\nready to start with repo: ($branch, $builder)\n";
    }
else
    {
    print STDERR "\nmissing parameter: branch\n";
    print_HTML_Page( buildbotQuery::html_ERROR_msg($usage), '&nbsp;', '&nbsp;', $err_color );
    exit;
    }



#### S T A R T  H E R E 

print STDERR "calling  buildbotReports::last_done_build($builder, $branch)";
my ($bldstatus, $bldnum, $rev_numb, $bld_date, $is_running) = buildbotReports::last_done_build($builder, $branch);
print STDERR "according to last_done_build, is_running = $is_running\n";

if ($bldnum < 0)
    {
    print_HTML_Page( buildbotQuery::html_RUN_link( $builder, 'no build yet'),
                     buildbotReports::is_running($is_running),
                     $builder,
                     $note_color );
    }
elsif ($bldstatus)
    {
    print_HTML_Page( buildbotQuery::html_OK_link( $builder, $bldnum, $rev_numb, $bld_date),
                   # $is_running,
                     buildbotReports::is_running($is_running),
                     $builder,
                     $good_color );
    
    print STDERR "GOOD: $bldnum\n"; 
    }
else
    {
    print STDERR "FAIL: $bldnum\n"; 
   
    my $background; 
    if ( $is_running == 1 )
        {
        $bldnum += 1;
        $background = $warn_color;
        }
    else
        {
        $background = $err_color;
        }
    print_HTML_Page( buildbotReports::is_running($is_running),
                     buildbotQuery::html_FAIL_link( $builder, $bldnum, $is_running, $bld_date),
                     $builder,
                     $background );
    }


# print "\n---------------------------\n";
__END__
