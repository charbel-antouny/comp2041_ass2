#!/usr/bin/perl -w

# written by Charbel Antouny 2014
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/LOVE2041/

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Data::Dumper;  
use List::Util qw/min max/;
warningsToBrowser(1);

print page_header();

# some globals used through the script
$debug = 1;								# THIS SHOULD BE 0 WHEN ASSIGNMENT FINISHED!
$students_dir = "./students30";			# CHANGE BACK TO ORIGINAL: './students'
%students = ();
@students = glob("$students_dir/*");

home_page();
#print browse_screen();
print page_trailer();

sub home_page {
	my $x = param('x') || 0;
	my $max;
	($x + 9 > $#students) ? ($max = $#students) : ($max = $x + 9);
	param('x', $x+10);
	print start_form,"\n",
	"<div class='jumbotron'>\n",
  	"<div class='page-header'>\n",
  	"<h2>Welcome to UNSWLUV! <small>Dating for UNSW students</small></h2>\n",
	"</div>\n",
  	"<p>Lonely? Looking for love?<br>You've come to the right place!<br><br>",
  	"Choose a profile to get started <span class='glyphicon glyphicon-heart'></span></p>\n",
  	"</div><br>\n";
	if ($x <= $max) {
		print "<div><ul>\n";
		for ($x..$max) {
			my $stud = $students[$_];
			$stud =~ s/\.\/students[0-9]*\///;
			print "<li>$stud</li>\n";	#maybe just make small buttons?
		}
		print "</ul></div><br><br>\n";
		print hidden('x', $x+10);
	} else {
		print "<div><p style='padding-left: 15px; padding-bottom: 20px'>You've reached the end. ",
		"Click 'More Students' to start from the beginning!</p></div>\n",
		hidden('x', 0),"\n";
	}
	print "<div class='col-md-2 col-lg-2'>\n",
	"<input class='btn btn-primary' type='submit' name='More Students' value='More Students'></div>\n",
	"<br><br>\n",
	end_form;
}

sub browse_screen {
	my $n = param('n') || 0;
	$n = min(max($n, 0), $#students);
	param('n', $n + 1);
	my $student_to_show  = $students[$n];
	my $profile_filename = "$student_to_show/profile.txt";
	my $profilePic = $student_to_show;
	$profilePic =~ s/\.\///;
	if (-e "$profilePic/profile.jpg") {
		$profilePic = "$profilePic/profile.jpg";
	} else {
		$profilePic = "";
	}
	open F, "$profile_filename" or die "can not open $profile_filename: $!";
	my $currCat;
	for my $line (<F>) {
		if ($line =~ m/^(\w*):/) {
			$currCat = $1;
			$currCat =~ s/(.*?)_(.*?)/$1 $2/g if ($currCat =~ m/_/);
		} else {
			push @{$students{$student_to_show}{$currCat}}, $line;
		}
	}
	close F;

	print start_form, "\n",
		"<div style='text-align:center'><img src=\"$profilePic\" class=\"img-circle\"/></div>\n",
		"<div><p class='username'>$students{$student_to_show}{username}[0]</p></div><br>\n",
		"<div class='table-centred'><table class=\"table table-striped\">\n";
		foreach my $key (sort keys %{$students{$student_to_show}}) {
			if ($key eq "courses" or $key eq "name" or $key eq "password" or $key eq "email" or $key eq "username") {
				next;
			}
			print "<tr>\n";
			print "<td style=\"font-weight:bold\">$key</td>\n";
			print "<td>";
			foreach my $item (sort @{$students{$student_to_show}{$key}}) {
				print "$item";
			}
			print "</td>\n";
			print "</tr>\n";
		}
		print "</table></div>\n";
	return
		hidden('n', $n + 1),"\n",
		"<br>\n",
		"<div style='text-align: center'><input class='btn btn-primary' type='submit' name='Next Student' value='Next Student'></div>\n",
		"<br><br>\n",
		end_form, "\n";
}

# HTML placed at top of every screen
sub page_header {
	return 
		header,
		"<!DOCTYPE html\n",
		"PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"\n",
	 	"\"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n",
   		"<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en-US\" xml:lang=\"en-US\">\n",
		"<head>\n",
		"<title>UNSWLUV</title>\n",
		"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=iso-8859-1\"/>\n",
		"<link rel='stylesheet' href='formatting.css' type='text/css'/>\n",
		# Bootstrap start --> getbootstrap.com
		"<script src='//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js'></script>\n",
		"<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css'>\n",
		"<link href='//netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css' rel='stylesheet'>\n",
		# Bootstrap end
		"</head>\n",
		"<body>\n",
		"<div><h1 class='pgTitle'>UNSWLUV</h1></div>\n";
}

# HTML placed at bottom of every screen
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
sub page_trailer {
	my $html = "";
	$html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
	$html .= end_html;
	return $html;
}