{
  frontend = {
    account = {
      user = "gitlab-runner-frontend";
      uid = 1001;
      home = "/home/gitlab-runner-frontend";
      subUid = {
        start = 165536;
        count = 65536;
      };
      subGid = {
        start = 165536;
        count = 65536;
      };
    };

    gitlab = {
      url = "https://gitlab.wke.csie.ncnu.edu.tw";
      healthUrl = "https://gitlab.wke.csie.ncnu.edu.tw/users/sign_in";
    };

    runner = {
      name = "A-frontend-podman";
      serviceName = "gitlab-runner-frontend";
      managerImage = "docker.io/gitlab/gitlab-runner:v18.10.1";
      tags = [
        "frontend"
        "podman"
      ];
      concurrent = 1;
      cpus = "2";
      memory = "4g";
      shmSizeBytes = 1073741824;
      pullPolicy = "if-not-present";
      defaultJobImage = "docker.io/library/node:22.22.0-bookworm";
      allowedImages = [
        "docker.io/library/node:*"
        "mcr.microsoft.com/playwright:*"
        "docker.io/curlimages/curl:*"
      ];
      allowedServices = [ ];
    };

    network = {
      requiredInterface = "tailscale0";
      dns = "100.100.100.100";
    };

    validation = {
      image = "docker.io/curlimages/curl:8.12.1";
    };
  };

  dotnet = {
    account = {
      user = "gitlab-runner-dotnet";
      uid = 1002;
      home = "/home/gitlab-runner-dotnet";
      subUid = {
        start = 231072;
        count = 65536;
      };
      subGid = {
        start = 231072;
        count = 65536;
      };
    };

    gitlab = {
      url = "https://gitlab.wke.csie.ncnu.edu.tw";
      healthUrl = "https://gitlab.wke.csie.ncnu.edu.tw/users/sign_in";
    };

    runner = {
      name = "A-dotnet-podman";
      serviceName = "gitlab-runner-dotnet";
      managerImage = "docker.io/gitlab/gitlab-runner:v18.10.1";
      tags = [
        "dotnet"
        "podman"
      ];
      concurrent = 1;
      cpus = "4";
      memory = "6g";
      shmSizeBytes = 1073741824;
      pullPolicy = "if-not-present";
      defaultJobImage = "mcr.microsoft.com/dotnet/sdk:10.0.302-noble";
      allowedImages = [
        "mcr.microsoft.com/dotnet/sdk:*"
        "mcr.microsoft.com/dotnet/runtime:*"
        "mcr.microsoft.com/dotnet/aspnet:*"
      ];
      allowedServices = [ "mcr.microsoft.com/mssql/server:*" ];
    };

    network = {
      requiredInterface = "tailscale0";
      dns = "100.100.100.100";
    };

    validation = {
      image = "docker.io/curlimages/curl:8.12.1";
    };
  };
}
