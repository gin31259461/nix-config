{
  locale = {
    generated = [
      "en_US.UTF-8"
      "zh_TW.UTF-8"
    ];
    lang = "en_US.UTF-8";
  };
  timeZone = "Asia/Taipei";
  hostname.enable = true;
  firewall.rules = [
    {
      protocol = "tcp";
      fromPort = 7777;
    }
    {
      protocol = "udp";
      fromPort = 7777;
    }
    {
      protocol = "tcp";
      fromPort = 47990;
    }
    {
      protocol = "udp";
      fromPort = 27031;
      toPort = 27036;
    }
  ];
}
