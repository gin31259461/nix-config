{
  lib,
  raw ? { },
}:
let
  result =
    (lib.evalModules {
      modules = [
        { options = import ./system-settings-options.nix { inherit lib; }; }
        raw
      ];
    }).config;
in
assert lib.assertMsg (
  result.locale == null || builtins.elem result.locale.lang result.locale.generated
) "LANG must be generated";
assert lib.assertMsg (
  result.locale == null || lib.unique result.locale.generated == result.locale.generated
) "duplicate generated locales";
assert lib.assertMsg (
  result.power == null || result.power.powerKey != null || result.power.lidSwitch != null
) "power must select an event";
assert lib.assertMsg (
  result.firewall == null
  || lib.all (r: r.toPort == null || r.toPort >= r.fromPort) result.firewall.rules
) "invalid firewall port range";
assert lib.assertMsg (
  result.firewall == null || lib.unique result.firewall.rules == result.firewall.rules
) "duplicate firewall rules";
builtins.deepSeq result result
