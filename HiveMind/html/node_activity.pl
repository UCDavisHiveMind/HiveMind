#!/usr/bin/perl
#
#
use CGI;

$errorMessage = "";


print <<HTML;
Content-type: text/html

<head>
        <title> Text area example</title>
	<meta http-equiv="refresh" content="10" />
	<style type="text/css">
        th
        {
	    background-color:gray;
        }
        td
        {
	    width:100px;
        }
	body
	{
	    background-color:#d0e4fe;
            font-size:12px;
            font-family:"Times New Roman";
	}
        </style>

</head>
<body>
HTML


my %skey_hash;
my %node_stats;
#my @AoI = qw( u_port u_service u_user u_chron p_pw_cmplx p_pw_age );
my @AoI = qw( u_service u_port u_priv_acct u_task u_ext_src u_ext_dst u_inf_src u_inf_dst suspicious_file_by_name suspicious_file_    remnants_location suspicious_file_remnants_type unexected_privileges unexpected_connections_from_internet unexpe    cted_connections_to_infrastructure unexpected_connections_to_internet unexpected_device unexpected_gateway unexp    ected_group unexpected_group_id unexpected_interface unexpected_interface unexpected_IP_for_MAC unexpected_MAC_f    or_IP unexpected_membership unexpected_packet_volume unexpected_port unexpected_process unexpected_process_owner     unexpected_process_path unexpected_route unexpected_schedule unexpected_service unexpected_task unexpected_user     unexpected_user_id );

load_session_keys();

print "<table border='1'>";

#- print header
print "<TR  align='center'>";
print "<th>Device</th><th>last check</th>";
foreach my $v ( @AoI ) {
    $v =~ s/_/ /g;
    print "<th style='width:100px'>$v</th>"; 
}
print "</TR>\n";

#- for each observed device, print the AoIs seen (and other stats)
foreach my $node (sort my_cmp keys %skey_hash) {
    next unless $node =~ /^node-/;

    $value = $skey_hash{$node};

    #- unparse all sub-values for this node
    my @sub_vals = split /,/,$value;
    foreach my $sv ( @sub_vals ){
	my ($k,$v) = split /:/,$sv;
	$node_stats{$node}{$k}=$v;
    }
    print "<TR><TD align='right'>$node</td>";
    $v = ($_ = $node_stats{$node}{last_check}) ? $_ : '-';
    print "<td align='center'>$v</TD>";

    #foreach my $aoi ( @AoI ) {
    foreach my $aoi ( 1..scalar(@AoI) ) {
	$v = ($_ = $node_stats{$node}{$aoi}) ? $_ : '-';
	print "<td align='center'>$v</TD>";
    }
    print "</TR>\n";

}

print "</table>";


print "
</body>
";                              # Main body of program ends here



sub my_cmp {
  ($x) = $a =~ /^node-(\S+)/;
  ($y) = $b =~ /^node-(\S+)/;
  
  if ($x && $y) {
      return $x <=> $y;
  } else {
      return $a <=> $b;
  }
}

  
#- get prior session keys
sub load_session_keys {
    open SK,"</tmp/session_keys.txt";
    $session_keys = <SK>;
    chomp $session_keys;
    close SK;
    @key_list = split /;/, $session_keys;
    foreach ( @key_list ) {
	($name,$value) = split /=/,$_;
	$skey_hash{$name} = $value;
    }
}

