# Wi-Fi hotspot preparation and recovery

The [Host declaration](../hosts/arch/system.nix) supplies hotspot defaults.
Arch adopts one existing NetworkManager connection by its unique name, resolves
its UUID, and changes only declared public properties. It preserves security
settings, credentials, UUID and unowned connection properties. The prepared
connection must use AP mode and WPA personal security (`wpa-psk` or `sae`).

## Prepare a machine

Before deploying with hotspot management selected, install and start the native
NetworkManager service and prepare the named Wi-Fi AP using the native connection
editor. Set its password there and save the connection for unattended system use.
Keep credentials in NetworkManager's protected system storage; do not put them
in the checkout, an `.env`, Nix expressions, shell arguments or logs.

Ensure the declared wireless and uplink interfaces exist. Stop any different
connection using the wireless interface before deployment. Duplicate connection
names, a non-AP profile, unsupported security or an occupied interface fail
preflight. Missing credentials are reported by activation without revealing
native output; the adapter never reads the password to inspect readiness.

The existing Arch-Hyprland profile already meets this preparation requirement.
For another machine, change the Host values or set `networking.hotspot.enable =
false` in `configuration.nix` until its connection is prepared. Builds and flake
checks use isolated fixtures and never inspect or create local connections.

## Deploy and verify

Use the normal [Arch deployment workflow](deployment.md). Routine deployment
requires the selected native inventory, including `iw`, to be installed; missing
packages exit 3. Only the explicit update workflow installs packages.

The controller holds its deployment lock during adoption, UFW convergence and
activation. A healthy repeat does not modify or restart the hotspot. Changing
public settings on an active hotspot reapplies its connection and can briefly
disconnect clients. Inactive hotspots start when `autoconnect` is true; false
updates the saved setting without stopping an active hotspot. Runtime address,
SSID and channel drift trigger reactivation.

After an authorized deployment, inspect public status and connect a client:

```bash
nmcli -f DEVICE,TYPE,STATE device status
iw dev wlp15s0 info
sudo ufw status verbose
```

The client should acquire an address, resolve DNS and reach the Internet. The
scoped IPv4 exceptions allow DHCP on the hotspot, DNS from its subnet to its
gateway, and forwarding from that subnet through the declared uplink. They do
not allow arbitrary access to the host or other egress interfaces. IPv6 shared
mode is preserved, but this capability does not add IPv6 forwarding exceptions.

## Recover interrupted work

Failures retain private pending receipts under `/var/lib/nix-config/arch/`.
Correct the reported preparation or activation issue and rerun deployment.
The adapter adopts matching manually added UFW rules and repairs missing kernel
rules from persistent UFW configuration without duplicating rules. It leaves
NetworkManager NAT and other owners' firewall chains intact.

Disabling hotspot or NetworkManager management leaves the connection, rules,
credentials and pending work untouched. Changing interface, subnet or uplink
adds the newly required rules; it does not retire old exceptions. Review and
retire superseded rules separately when explicitly intended. Do not disable the
whole firewall to recover hotspot connectivity.
