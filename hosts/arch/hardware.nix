{
  graphics = "amd";
  openrazer = true;
  initramfsModules = [
    "usbhid"
    "xhci_pci"
    "amdgpu"
  ];
  initramfsImages = [ "/boot/initramfs-linux.img" ];
}
