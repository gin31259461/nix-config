# Adopt a Wi-Fi hotspot

The Arch system adapter manages public properties of one existing NetworkManager AP connection, selected by its unique connection name. NetworkManager retains the UUID, WPA credentials, security material and unrelated profile fields. The adapter never reads or prints the password.

## Prepare the native connection

Before enabling `networking.hotspot`, make sure NetworkManager is installed and running. Create the named AP profile with `nmcli`, configure WPA personal security and its password in NetworkManager's protected storage, and check that both declared wireless and uplink interfaces exist. Another connection must not occupy the wireless interface. Keep credentials out of Nix, Git, shell arguments and logs.

The public options live in `configuration.nix`; use [configuration](configuration.md) to inspect resolved values. If a machine has different hardware, override `networking.hotspot.interface` and `networking.hotspot.uplink`, or disable the capability. A selected hotspot with either declared interface missing fails core preflight before mutation. Duplicate names, non-AP profiles, insecure or conflicting ownership and failed native queries also fail.

## Deploy and verify

```bash
just arch-workstation
nmcli -f DEVICE,TYPE,STATE device status
sudo ufw status verbose
```

If declared native packages are missing, use `just arch-workstation update` after reviewing the package operation. Changing AP properties may reactivate the connection and briefly disconnect clients; an unchanged healthy connection stays running. When firewall management is enabled, the adapter derives scoped IPv4 DHCP, gateway DNS and forwarding rules for the selected subnet and uplink. NetworkManager owns NAT; default deny policy outside those rules remains in effect.

Connect a client and check address assignment, DNS and Internet routing. To inspect the radio, use `iw dev <declared-wireless-interface> info` with the actual declared interface name.

## Recover

Interrupted native actions retain pending markers under `/var/lib/nix-config/arch/`. Correct the reported conflict or missing prerequisite and rerun deployment. Do not remove markers merely to make a retry pass. Disabling hotspot management leaves existing NetworkManager profiles, credentials and runtime state intact. If a declaration changes interface, subnet or uplink, review any obsolete manual rules explicitly; deployment does not infer retirement intent.
