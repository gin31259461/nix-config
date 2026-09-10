{
  source = {
    repository = "https://github.com/ggml-org/llama.cpp.git";
    revision = "434ddbbc0e30522e897670681e503b797c12b7c1";
    grammarRepetitionThreshold = 20000;
    installPrefix = "/opt/llama-cpp-opencode";
  };
  defaultModel = "qwen3.5-35b-a3b-mxfp4";
  models."qwen3.8-27b-ud-q3-k-xl" = {
    artifact = {
      id = "Qwen3.8-27B-GGUF:UD-Q3_K_XL";
      repository = "unsloth/Qwen3.8-27B-GGUF";
      revision = "4ca720788d1e01f1bff70c033e0d0028fd02e502";
      file = "Qwen3.8-27B-UD-Q3_K_XL.gguf";
      path = "/var/lib/llama/models/Qwen3.8-27B-UD-Q3_K_XL.gguf";
      sha256 = "8c2a45ff85e7674ca185ec8eb6cdeab0e617ed9d8018caed0b64380eb2a67a5e";
    };
    runtime = {
      contextSize = 98304;
      fitTarget = 1024;
      cacheTypeK = "q8_0";
      cacheTypeV = "q8_0";
      batchSize = 2048;
      microBatchSize = 512;
      parallel = 1;
    };
  };
  models."qwen3.5-35b-a3b-mxfp4" = {
    artifact = {
      id = "Qwen3.5-35B-A3B-GGUF:MXFP4_MOE";
      repository = "unsloth/Qwen3.5-35B-A3B-GGUF";
      revision = "bc014a17be43adabd7066b7a86075ff935c6a4e2";
      file = "Qwen3.5-35B-A3B-MXFP4_MOE.gguf";
      path = "/var/lib/llama/models/Qwen3.5-35B-A3B-MXFP4_MOE.gguf";
      sha256 = "0f135a59159030f4710477abc6f9922d2f13552c85bff736deaaef71023cd770";
    };
    runtime = {
      contextSize = 98304;
      fitTarget = 1024;
      cacheTypeK = "q8_0";
      cacheTypeV = "q8_0";
      batchSize = 2048;
      microBatchSize = 512;
      parallel = 1;
    };
  };
  server = {
    host = "127.0.0.1";
    port = 11434;
    modelsMax = 1;
  };
  proxy.localPort = 11435;
}
