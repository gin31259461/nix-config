# Wi-Fi hotspot

The Arch system adapter adopts one existing NetworkManager AP connection by its
unique connection name. It manages declared public properties while preserving
the UUID, credentials, security material, and unrelated NetworkManager fields.

## Prepare

Before enabling hotspot management:

1. Ensure NetworkManager is installed and running.
2. Create the declared AP connection with native NetworkManager tools (`nmcli`).
3. Configure WPA personal security and the password in NetworkManager.
4. Ensure the declared wireless and uplink interfaces exist.
5. Stop any other connection that occupies the hotspot interface.

Credentials must remain in NetworkManager's protected system storage. Do not put
them in Nix expressions, environment files, shell arguments, Git, or logs.

The adapter rejects duplicate connection names, non-AP profiles, unsupported
security, and conflicting interface use. Source builds and flake checks use
fixtures and never inspect the live NetworkManager configuration.

## Deploy

```bash
just arch-workstation
```

Use `just arch-workstation update` if declared native packages are missing.
Changing hotspot settings can reactivate an active connection and briefly
disconnect clients. An unchanged healthy configuration is left running.

When firewall management is enabled, the system adapter derives scoped IPv4
rules for DHCP, gateway DNS, and forwarding from the hotspot subnet through the
declared uplink. NetworkManager owns NAT. Default incoming and routed deny policy
remains in effect outside those rules.

If the declared wireless interface or uplink does not exist on the host hardware,
hotspot convergence is safely skipped with a highlighted notice without failing
workstation deployment. Set `networking.hotspot.enable = false;` or override
`networking.hotspot.interface` / `networking.hotspot.uplink` in `configuration.nix`
for machines with different hardware.

## Verify

```bash
nmcli -f DEVICE,TYPE,STATE device status
iw dev wlp15s0 info
sudo ufw status verbose
```

Connect a client and verify IP address assignment, DNS resolution, and Internet
routing. Adjust interface names to match your Host declaration if they differ.

## Recovery

Interrupted network and firewall actions retain pending markers under:

```text
/var/lib/nix-config/arch/
```

Correct the reported prerequisite or runtime problem and rerun deployment.
**Do not delete pending markers as a recovery shortcut.**

Disabling hotspot or NetworkManager management leaves existing connections,
credentials, and runtime state untouched. Changing interface, subnet, or uplink
can require explicit cleanup of obsolete rules after the new declaration is
verified; deployment does not infer retirement intent.
