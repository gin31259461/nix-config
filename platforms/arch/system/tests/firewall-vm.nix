{ pkgs }:
let
  ufw = import ./package.nix { inherit pkgs; };
  manifest =
    (import ../default.nix {
      inherit pkgs;
      inherit (pkgs) lib;
      hostName = "fixture";
      config = import ../../../../lib/system-settings.nix {
        inherit (pkgs) lib;
        raw.firewall = (import ../../../../hosts/arch/system.nix).firewall;
      };
    }).manifest;
in
pkgs.testers.runNixOSTest {
  name = "arch-ufw-coexistence";
  nodes.machine = { ... }: {
    networking.firewall.enable = false;
    virtualisation.memorySize = 1024;
    boot.kernel.sysctl."net.ipv4.ip_forward" = 1;
    environment.systemPackages = [
      pkgs.python3
      pkgs.iptables
      pkgs.nftables
      pkgs.iproute2
      pkgs.socat
    ];
    systemd.services.ufw = {
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStart = "${ufw}/lib/ufw/ufw-init start quiet";
      };
    };
  };
  testScript = ''
    start_all()
    machine.wait_for_unit("multi-user.target")
    machine.succeed("mkdir -p /etc/ufw /etc/default /usr/bin")
    machine.succeed("cp -r ${ufw}/etc/ufw/* /etc/ufw/; cp ${ufw}/etc/default/ufw /etc/default/ufw; chmod -R u+w /etc/ufw /etc/default/ufw")
    machine.succeed("ln -s ${ufw}/bin/ufw-fixture /usr/bin/ufw")
    for command in ["systemctl", "iptables", "ip6tables"]:
        machine.succeed(f"ln -s $(command -v {command}) /usr/bin/{command}")
    # Separate namespaces exercise packets without exposing ports on the host.
    machine.succeed("ip netns add client; ip link add inside type veth peer name outside; ip link set outside netns client")
    machine.succeed("ip addr add 192.0.2.1/24 dev inside; ip -6 addr add fd00:1::1/64 dev inside; ip link set inside up")
    machine.succeed("ip netns exec client ip addr add 192.0.2.2/24 dev outside; ip netns exec client ip -6 addr add fd00:1::2/64 dev outside; ip netns exec client ip link set outside up; ip netns exec client ip link set lo up")
    # Simulate independently owned Tailscale/libvirt chains and nftables NAT table.
    machine.succeed("iptables -N ts-input; iptables -I INPUT -j ts-input; iptables -N LIBVIRT_FWI; iptables -I FORWARD -j LIBVIRT_FWI")
    machine.succeed("nft add table ip fixture_nat; nft 'add chain ip fixture_nat postrouting { type nat hook postrouting priority srcnat; }'; nft add rule ip fixture_nat postrouting ip saddr 198.51.100.0/24 masquerade")
    machine.succeed("/usr/bin/ufw allow in 12345/tcp")
    adapter = "${pkgs.python3}/bin/python3 ${../.}/runtime.py ${manifest} converge"
    result, output = machine.execute(adapter)
    if result:
        print(machine.execute("/usr/bin/ufw status verbose"))
        print(output)
        raise Exception("adapter did not converge")
    machine.succeed("/usr/bin/ufw status verbose | grep 'Status: active'")
    machine.succeed("iptables -C INPUT -j ts-input; iptables -C FORWARD -j LIBVIRT_FWI; nft list table ip fixture_nat | grep masquerade")
    machine.succeed("socat TCP4-LISTEN:7777,reuseaddr,fork EXEC:cat >/dev/null 2>&1 & socat TCP6-LISTEN:7777,ipv6only=1,reuseaddr,fork EXEC:cat >/dev/null 2>&1 & socat TCP4-LISTEN:8888,reuseaddr,fork EXEC:cat >/dev/null 2>&1 & socat TCP6-LISTEN:8888,ipv6only=1,reuseaddr,fork EXEC:cat >/dev/null 2>&1 &")
    machine.wait_until_succeeds("ip netns exec client sh -c 'echo allowed | socat -T2 - TCP4:192.0.2.1:7777,connect-timeout=2' | grep allowed")
    machine.wait_until_succeeds("ip netns exec client sh -c 'echo allowed | socat -T2 - TCP6:[fd00:1::1]:7777,connect-timeout=2' | grep allowed")
    machine.fail("ip netns exec client sh -c 'echo denied | socat -T2 - TCP4:192.0.2.1:8888,connect-timeout=2' | grep denied")
    machine.fail("ip netns exec client sh -c 'echo denied | socat -T2 - TCP6:[fd00:1::1]:8888,connect-timeout=2' | grep denied")
    machine.succeed("ip netns exec client ping -c1 192.0.2.1; ip netns exec client ping -6 -c1 fd00:1::1")
    # Exercise every declared TCP port and both UDP range boundaries for both families.
    for family, address in [("4", "192.0.2.1"), ("6", "[fd00:1::1]")]:
        ipv6 = ",ipv6only=1" if family == "6" else ""
        machine.succeed(f"socat TCP{family}-LISTEN:47990{ipv6},reuseaddr,fork EXEC:cat >/dev/null 2>&1 &")
        machine.wait_until_succeeds(f"ip netns exec client sh -c 'echo allowed | socat -T2 - TCP{family}:{address}:47990,connect-timeout=2' | grep allowed")
        for port in [7777, 27031, 27036, 27037]:
            machine.succeed(f"socat UDP{family}-RECVFROM:{port}{ipv6},reuseaddr,fork EXEC:cat >/dev/null 2>&1 &")
            probe = f"ip netns exec client sh -c 'echo probe | socat -T2 - UDP{family}:{address}:{port}' | grep probe"
            if port == 27037:
                machine.fail(probe)
            else:
                machine.wait_until_succeeds(probe)
    machine.succeed("echo loopback | socat -T2 - TCP4:127.0.0.1:8888,connect-timeout=2 | grep loopback")
    # NAT/forwarding belongs to the virtualization owner, not UFW configuration.
    machine.succeed("ip netns add guest; ip link add guestbridge type veth peer name guestif; ip link set guestif netns guest")
    machine.succeed("ip addr add 198.51.100.1/24 dev guestbridge; ip link set guestbridge up; ip netns exec guest ip addr add 198.51.100.2/24 dev guestif; ip netns exec guest ip link set guestif up; ip netns exec guest ip link set lo up; ip netns exec guest ip route add default via 198.51.100.1")
    machine.succeed("ip netns exec client socat TCP4-LISTEN:9999,reuseaddr,fork EXEC:cat >/dev/null 2>&1 &")
    machine.fail("ip netns exec guest sh -c 'echo routed | socat -T2 - TCP4:192.0.2.2:9999,connect-timeout=2' | grep routed")
    machine.succeed("iptables -A LIBVIRT_FWI -s 198.51.100.0/24 -j ACCEPT; iptables -A LIBVIRT_FWI -d 198.51.100.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT")
    nat_probe = "ip netns exec guest sh -c 'echo routed | socat -T2 - TCP4:192.0.2.2:9999,connect-timeout=2' | grep routed"
    machine.wait_until_succeeds(nat_probe)
    # Healthy repeat preserves rule files and repair restores a deleted kernel rule.
    machine.succeed("sha256sum /etc/ufw/user.rules /etc/ufw/user6.rules > /tmp/rules.before")
    assert "0 files updated, 0 runtime actions" in machine.succeed(adapter)
    machine.succeed("sha256sum --check /tmp/rules.before")
    machine.succeed("iptables -D ufw-user-input -p tcp --dport 7777 -j ACCEPT")
    machine.succeed(adapter)
    machine.succeed("iptables -C ufw-user-input -p tcp --dport 7777 -j ACCEPT; iptables -C ufw-user-input -p tcp --dport 12345 -j ACCEPT")
    machine.succeed("iptables -C INPUT -j ts-input; iptables -C FORWARD -j LIBVIRT_FWI; nft list table ip fixture_nat | grep masquerade")
    machine.succeed(nat_probe)
  '';
}
