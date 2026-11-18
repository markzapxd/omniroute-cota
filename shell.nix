{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (p: [ p.pygobject3 ]))
    pkgs.gobject-introspection pkgs.gtk4 pkgs.libsecret
    pkgs.cmake pkgs.pkg-config pkgs.qt6.qtbase pkgs.qt6.qtdeclarative
  ];
  GI_TYPELIB_PATH = "${pkgs.gtk4}/lib/girepository-1.0:${pkgs.libsecret}/lib/girepository-1.0:${pkgs.glib.out}/lib/girepository-1.0";
}
