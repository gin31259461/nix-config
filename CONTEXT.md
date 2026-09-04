# Nix Configuration

This context describes how machine identity, reusable policy, and optional
capabilities compose into the deployable Arch configuration.

## Language

**Host**:
A real machine and its final deployable configuration.
_Avoid_: Platform configuration, environment

**Platform**:
The operating-system mechanism that realizes a host, currently Arch.
_Avoid_: Host, distribution profile

**Profile**:
A reusable bundle of general-purpose configuration selected by hosts.
_Avoid_: Platform, feature

**Module**:
An optional capability with one interface and platform-specific adapters when
required.
_Avoid_: Profile, service bundle

**Adapter**:
The implementation of a module or host policy for one platform.
_Avoid_: Platform profile

**Login user**:
A human account selected and owned by a host.
_Avoid_: Service account

**Service account**:
A non-human identity owned by the module that requires it.
_Avoid_: Login user

**Instance**:
One configured occurrence of a module on a host.
_Avoid_: Profile

**Deployment target**:
A buildable and activatable host/profile pairing, named `<host>-<profile>` and
associated with one login user.
_Avoid_: Host, profile

**Required interface**:
A network interface that must be usable for an operation to proceed; it does
not imply that traffic is bound or forcibly routed through that interface.
_Avoid_: VPN interface, egress interface
