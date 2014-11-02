#!/usr/bin/perl -w

# written by Charbel Antouny 2014
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/LOVE2041/

use CGI qw/:all/;
use CGI::Session;
use CGI::Cookie;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Data::Dumper;
warningsToBrowser(1);

# some globals used through the script
$debug = 0;
$students_dir = "./students";
%students = ();
$loginFlag = 0;
$year = 2014;
@students = glob("$students_dir/*");	# format of elements is "./students[30]/USERNAME"

# store all student info in a hash
for (0..$#students) {
	my $student_to_show  = $students[$_];
	my $profile_filename = "$student_to_show/profile.txt";
	open F, "$profile_filename" or die "can not open $profile_filename: $!";
	my $currCat;
	for my $line (<F>) {
		chomp $line;
		$line =~ s/^\s*//g;
		if ($line =~ m/^(\w*):/) {
			$currCat = $1;
			$currCat =~ s/(.*?)_(.*?)/$1 $2/g if ($currCat =~ m/_/);
		} else {
			push @{$students{$student_to_show}{$currCat}}, $line;
		}
	}
	close F;
}

$cgi = CGI->new;
(!defined param('logoutbtn')) ? ($sid = $cgi->cookie("CGISESSID") || undef) : ($sid = undef);
$session = new CGI::Session(undef, $sid, {Directory=>'/tmp'});
$session->expire('+30m');
$loggedIn = $session->param('loggedIn') || 0;
$cookie = $cgi->cookie(-name => 'CGISESSID', -value => $session->id, -expires => '+30m');
if (defined param('loginbtn')) {
	my $user = param('loginUser');
	$username = $user;
	my $pass = param('loginPass');
	$pass =~ s/[^a-zA-Z0-9]*//g;
	$user = "$students_dir/$user";
	if (defined $students{$user} and $pass eq $students{$user}{password}[0]) {
    	$session->param('loggedIn', 1);
    	$loggedIn = 1;
		$session->param('username', $username);
		$loginFlag = 1;
	} else {
		print header();
		page_header();
		$loginFlag = 1;
		print "<div class=\"alert alert-danger\" role=\"alert\">",
			"Oops, looks like your username or password is wrong. Please try again.</div>\n";
	}
}

if (defined param('logoutbtn')) {
	$session->param('loggedIn', 0);
	$session->clear('scores');
	$loggedIn = 0;
}
if (!$loggedIn) {
	print header() if (!$loginFlag);
	page_header() if (!$loginFlag);
	login_page();
} else {
	$username = $session->param('username') if (!defined $username);
	print $session->header();
	page_header();
	if (!defined param('Home')) {
		if (defined param('searchbtn')) {
			my $query = param('searchBar');
			$query =~ s/[^a-zA-Z0-9]*//g;
			search_users($query);
		} elsif (defined param('matchPrev') or defined param('matchNext') or defined param('matchbtn')) {
			match_user();
		} else {
			# check if a user profile has been selected
			my $stud = param('stud_username');
			if ($stud) {
				$stud = "$students_dir/${stud}";
				browse_screen($stud);
			} else {
				home_page();
			}
		}
	} else {
		home_page();
	}
}

print page_trailer();

sub login_page {
	# START BOOTSTRAP SIGNIN CSS -> getbootstrap.com/examples/signin
	print "<div class=\"container\" style='padding-top: 40px; padding-bottom: 40px'>\n",
    	"<form class=\"form-signin\" role=\"form\" method='POST'>\n",
        "<h2 class=\"form-signin-heading\">Please login</h2>\n",
        "<input type=\"text\" class=\"form-control\" placeholder=\"Username\" name='loginUser' required autofocus>\n",
        "<input type=\"password\" class=\"form-control\" placeholder=\"Password (letters & numbers only)\" name='loginPass' required>\n",
        "<label class=\"checkbox\" style='padding-left: 20px'>\n",
        "<input type=\"checkbox\" value=\"remember-me\"> Remember me</label>\n",
        "<button class=\"btn btn-lg btn-primary btn-block\" type=\"submit\" name='loginbtn'>Login</button>\n",
      	"</form></div>\n";
    # END BOOTSTRAP SIGNIN CSS
}

sub home_page {
	my $x = param('x') || 0;
	my $max;
	($x + 9 > $#students) ? ($max = $#students) : ($max = $x + 9);
	print start_form,"\n",
	"<div style='background:#ddd !important' class='jumbotron'>\n",
  	"<div class='page-header'>\n",
  	"<h2>Welcome to UNSWLUV! <small>Dating for UNSW students</small></h2>\n",
	"</div>\n",
  	"<p>Lonely? Looking for love?<br>You've come to the right place!<br><br>",
  	"Choose a profile to get started <span class='glyphicon glyphicon-heart'></span><br><br>",
  	"<span style='font-size: 14px'>Note: Please make sure cookies are enabled!</span></p>\n",
  	"</div>\n";
	if ($x <= $max) {
		print "<div><ul>\n";
		for ($x..$max) {
			my $stud = $students[$_];
			$stud =~ s/\.\/students[0-9]*\///;
			print "<li><input class='btn btn-link' type='submit' name='stud_username' value='${stud}'></li>\n";
		}
		print "</ul></div><br>\n";
		param('x', $x+10);
		print hidden('x', $x+10);
	} else {
		param('x', 0);
		print "<div><p style='padding-left: 15px; padding-bottom: 20px'>You've reached the end. ",
		"Click 'More Students' to start from the beginning!</p></div>\n",
		hidden('x', 0),"\n";
	}
	print "<div class='col-md-2 col-lg-2'>\n",
	"<input class='btn btn-primary' type='submit' name='moreStudents' value='More Students'></div>\n",
	"<br><br><br>\n",
	end_form;
}

sub match_user {
	my $user = "$students_dir/$username";
	my %scores = ();
	my $scoresRef = $session->param('scores') || undef;
	if (defined $scoresRef) {
		%scores = %{$scoresRef};
	}
	
	if (!defined %scores) {
		my %prefs = ();
		my $prefs_filename = "$user/preferences.txt";
		open F, "<$prefs_filename" or die "can't open $prefs_filename: $!";
		my $currCat;
		foreach my $line (<F>) {
			chomp $line;
			if ($line =~ m/^(\w*):/) {
				$currCat = $1;
				$currCat =~ s/(.*?)_(.*?)/$1 $2/g if ($currCat =~ m/_/);
			} else {
				$line =~ s/^\s*//g;
				push @{$prefs{$currCat}}, $line;
			}
		}
		close F;
		
		foreach my $stud (keys %students) {
			if ($stud eq $user) { next; }
			if (defined $prefs{age} and defined $students{$stud}{birthdate}) {
				my $minAge = $prefs{age}[1];
		 		my $maxAge = $prefs{age}[3];
		 		my $studAge = $students{$stud}{birthdate}[0];
		 		$studAge =~ m/\d{4}/;
		 		$studAge = $year - $&;
		 		if ($studAge >= $minAge and $studAge <= $maxAge) {
		 			$scores{$stud} += 20;
		 		}
		 		$minAge -= 2;
		 		$maxAge += 2;
		 		if ($studAge >= $minAge and $studAge <= $maxAge) {
		 			$scores{$stud} += 5;
		 		}
			} elsif (defined $students{$stud}{birthdate} and defined $students{$user}{birthdate}) {
				my $userAge = $students{$user}{birthdate}[0];
				$userAge =~ m/\d{4}/;
		 		$userAge = $year - $&;
		 		my $minAge = $userAge - 4;
		 		my $maxAge = $userAge + 4;
		 		my $studAge = $students{$stud}{birthdate}[0];
		 		$studAge =~ m/\d{4}/;
		 		$studAge = $year - $&;
		 		if ($studAge >= $minAge and $studAge <= $maxAge) {
		 			$scores{$stud} += 5;
		 		}
			}
			if (defined $prefs{gender} and defined $students{$stud}{gender}) {
				if ($prefs{gender}[0] eq $students{$stud}{gender}[0]) {
					$scores{$stud} += 50;
				}
			}
			if (defined $prefs{"hair colours"} and defined $students{$stud}{"hair colour"}) {
				foreach my $colour ($prefs{"hair colours"}) {
					if ($colour eq $students{$stud}{"hair colour"}[0]) {
						$scores{$stud} += 10;
					}
				}
			}
			if (defined $prefs{height} and defined $students{$stud}{height}) {
				my $minHeight = $prefs{height}[1];
				$minHeight =~ s/m//;
				my $maxHeight = $prefs{height}[3];
				$maxHeight =~ s/m//;
				my $studHeight = $students{$stud}{height}[0];
				$studHeight =~ s/m//;
				if ($studHeight >= $minHeight and $studHeight <= $maxHeight) {
					$scores{$stud} += 10;
				}
				$minHeight -= 0.05;
				$maxHeight += 0.05;
				if ($studHeight >= $minHeight and $studHeight <= $maxHeight) {
					$scores{$stud} += 5;
				}
			}
			if (defined $prefs{weight} and defined $students{$stud}{weight}) {
				my $minWeight = $prefs{weight}[1];
				$minWeight =~ s/kg//;
				my $maxWeight = $prefs{weight}[3];
				$maxWeight =~ s/kg//;
				my $studWeight = $students{$stud}{weight}[0];
				$studWeight =~ s/kg//;
				if ($studWeight >= $minWeight and $studWeight <= $maxWeight) {
					$scores{$stud} += 10;
				}
				$minHeight -= 5;
				$maxHeight += 5;
				if ($studWeight >= $minWeight and $studWeight <= $maxWeight) {
					$scores{$stud} += 5;
				}
			}
			if (defined $students{$user}{"favourite hobbies"} and defined $students{$stud}{"favourite hobbies"}) {
				foreach my $hobby ($students{$user}{"favourite hobbies"}) {
					if ($hobby ~~ $students{$stud}{"favourite hobbies"}) {
						$scores{$stud} += 7;
					}
				}
			}
			if (defined $students{$user}{"favourite TV shows"} and defined $students{$stud}{"favourite TV shows"}) {
				foreach my $show ($students{$user}{"favourite TV shows"}) {
					if ($show ~~ $students{$stud}{"favourite TV shows"}) {
						$scores{$stud} += 7;
					}
				}
			}
			if (defined $students{$user}{"favourite books"} and defined $students{$stud}{"favourite books"}) {
				foreach my $book ($students{$user}{"favourite books"}) {
					if ($book ~~ $students{$stud}{"favourite books"}) {
						$scores{$stud} += 7;
					}
				}
			}
		}
		$session->param('scores', \%scores);
	}
	print start_form;
	my $n = param('n') || 1;
	my $max;
	my $size = keys %scores;
	if (defined param('matchPrev')) {
		$n -= 20;
		param('n', $n+10);
		print hidden('n', $n+10);
		($n + 9 > $size) ? ($max = $size) : ($max = $n + 9);
	} else {
		($n + 9 > $size) ? ($max = $size) : ($max = $n + 9);
		param('n', $n+10);
		print hidden('n', $n+10);
	}
	my $count = 1;
	foreach my $stud (sort {$scores{$b} <=> $scores{$a}} keys %scores) {
		if ($count < $n) {
			$count += 1;
			next;
		} elsif ($count <= $max) {
			$tmp = $stud;
			$tmp =~ s/\.\/students[0-9]*\///g;
			print "<div class='table-centred'><table class='table table-bordered'>\n",
				"<tr>\n",
				"<td><div style='text-align:center'><img src=\"$stud/profile.jpg\" alt=\"No Image\" class='img-circle'/></div>\n",
				"<div><p class='username'>$students{$stud}{username}[0]</p></div></td>\n",
				"<td>Gender: $students{$stud}{gender}[0]\n" if (defined $students{$stud}{gender});
			print "Date of Birth: $students{$stud}{birthdate}[0]\n" if (defined $students{$stud}{birthdate});
			print "Degree: $students{$stud}{degree}[0]\n" if (defined $students{$stud}{degree});
			print "Height: $students{$stud}{height}[0]\n" if (defined $students{$stud}{height});
			print "Weight: $students{$stud}{weight}[0]\n" if (defined $students{$stud}{weight});
			print "<br><button class='btn btn-info' type='submit' name='stud_username' value=\"$tmp\">See More</button></p>\n",
				"</td></tr>\n";
			$count += 1;
		} else {
			last;
		}
	}
	print "</table></div>\n",
		"<br>\n",
		"<div class='text-center'>\n",
		"<div class='btn-group'>\n";
	if ($n >= 11) {
		print "<input class='btn btn-primary' type='submit' name='matchPrev' value='Back'>\n";
	}
	print "<input class='btn btn-primary' type='submit' name='home' value='Home'>\n";
	if ($max != $size) {
		print "<input class='btn btn-primary' type='submit' name='matchNext' value='Next'>\n";
	}
	print "</div></div><br><br>\n",
		end_form;
}

sub search_users {
	my $query = lc $_[0];
	my @results = ();
	foreach my $stud (keys %students) {
		$stud =~ s/\.\/students[0-9]*\///g;
		my $tmp = lc $stud;
		if ($tmp =~ m/${query}/) {
			push @results, $stud;
		}
	}
	print start_form,
		"<div class='table-centred'><table class='table table-bordered'>\n";
		foreach my $stud (sort @results) {
			$tmp = $stud;
			$stud = "$students_dir/${stud}";
			print "<tr>\n",
				"<td><div style='text-align:center'><img src=\"$stud/profile.jpg\" alt=\"No Image\" class='img-circle'/></div>\n",
				"<div><p class='username'>$students{$stud}{username}[0]</p></div></td>\n",
				"<td>Gender: $students{$stud}{gender}[0]\n" if (defined $students{$stud}{gender});
			print "Date of Birth: $students{$stud}{birthdate}[0]\n" if (defined $students{$stud}{birthdate});
			print "Degree: $students{$stud}{degree}[0]\n" if (defined $students{$stud}{degree});
			print "Height: $students{$stud}{height}[0]\n" if (defined $students{$stud}{height});
			print "Weight: $students{$stud}{weight}[0]\n" if (defined $students{$stud}{weight});
			print "<br><button class='btn btn-info' type='submit' name='stud_username' value=\"$tmp\">See More</button></p>\n",
				"</td></tr>\n";
		}
		print "</table></div>\n",
			"<br>\n",
			"<div style='text-align: center'><input class='btn btn-primary' type='submit' name='home' value='Home'></div>\n",
			"<br><br>\n",
			end_form;
}

sub browse_screen {
	my $currProfile = $_[0];
	if (-e "$currProfile/profile.jpg") {
		$currProfile = "$currProfile/profile.jpg";
	} else {
		$currProfile = "";
	}
	print start_form, "\n",
		"<div style='text-align:center'><img src='$currProfile' alt='No Image' class='img-circle'/></div>\n";
		$currProfile = $_[0];
		print "<div><p class='username'>$students{$currProfile}{username}[0]</p></div><br>\n",
		"<div class='table-centred'><table class=\"table table-striped\">\n";
	foreach my $key (sort keys %{$students{$currProfile}}) {
		if ($key eq "courses" or $key eq "name" or $key eq "password" or $key eq "email" or $key eq "username") {
			next;
		}
		print "<tr>\n";
		print "<td style=\"font-weight:bold\">$key</td>\n";
		print "<td>";
		foreach my $item (sort @{$students{$currProfile}{$key}}) {
			print "$item\n";
		}
		print "</td>\n";
		print "</tr>\n";
	}
	print "</table></div>\n",
		"<br>\n",
		"<div style='text-align: center'><input class='btn btn-primary' type='submit' name='home' value='Home'></div>\n",
		"<br><br>\n",
		end_form, "\n";
		param('stud_username', "");
}

# HTML placed at top of every screen
sub page_header {
	print
		"<!DOCTYPE html\n",
		"PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"\n",
	 	"\"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n",
   		"<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en-US\" xml:lang=\"en-US\">\n",
		"<head>\n",
		"<title>UNSWLUV</title>\n",
		"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=iso-8859-1\"/>\n",
		"<link rel='stylesheet' href='formatting.css' type='text/css'/>\n",
		# Bootstrap start --> getbootstrap.com
		#"<script src='//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js'></script>\n",
		"<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css'>\n",
		"<link href='//netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css' rel='stylesheet'>\n",
		# Bootstrap end
		"</head>\n",
		"<body style='background-color: #ededed; padding-top: 50px'>\n",
		# NAVBAR IS PRODUCED USING BOOTSTRAP --> getbootstrap.com
		"<nav class='navbar navbar-inverse navbar-fixed-top' role='navigation'>\n",
  		"<div class='container-fluid'>\n",
		"<div class='navbar-header'>\n",
		"<p class='navbar-brand'>UNSWLUV</p>\n",
		"</div>\n";
		if ($loggedIn) {
			print "<form class='navbar-form navbar-left' role='search' method='POST'>\n",
  			"<div class='form-group'>\n",
    		"<input type='text' class='form-control' placeholder='Search for Users' name='searchBar'>\n",
  			"</div>\n",
  			"<button type='submit' class='btn btn-info' name='searchbtn'>Submit</button>\n",
  			"<button type='submit' class='btn btn-success' name='matchbtn'>Match Me!</button>\n",
  			"</form>\n",
  			start_form,
			"<button type='submit' class='btn btn-info navbar-btn navbar-right' name='logoutbtn'>Logout</button>\n",
			"<p class='navbar-text navbar-right' style='padding-right: 10px'>Signed in as",
			"<button class='btn btn-link navbar-link' type='submit' name='stud_username' value=\"$username\">$username</button></p>\n",
			end_form;
		}
	print
		"</div></nav>\n",
		# END NAVBAR
		"<div><h1 id='pgTitle'>UNSWLUV</h1></div>\n";
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