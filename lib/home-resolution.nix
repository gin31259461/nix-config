{
  capabilities ? null,
  profiles ? import ../profiles,
  modules ? import ../modules/home,
}:
let
  resolve =
    registry: kind: name:
    if builtins.hasAttr name registry then registry.${name} else throw "unknown ${kind}: ${name}";
  selectedProfiles = builtins.filter (
    name: capabilities == null || capabilities.desktop.enable || name != "workstation"
  );
in
{
  profileModules = names: map (resolve profiles "profile") (selectedProfiles names);
  homeModules = names: map (resolve modules "home module") names;
}
