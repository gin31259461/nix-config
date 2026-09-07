{ lib, ... }:
{
  i18n.generated = lib.mkDefault [
    "en_US.UTF-8"
    "zh_TW.UTF-8"
  ];
  time.timeZone = lib.mkDefault "Asia/Taipei";
  networking.firewall.rules = lib.mkDefault [
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
