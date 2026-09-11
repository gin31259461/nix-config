{
  source = {
    repository = "https://github.com/ggml-org/llama.cpp.git";
    revision = "434ddbbc0e30522e897670681e503b797c12b7c1";
    grammarRepetitionThreshold = 20000;
    installPrefix = "/opt/llama-cpp-opencode";
  };
  defaultModel = "qwen3.8-27b-ud-q3-k-xl";
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
      reasoningEffort = "medium";
      temperature = 1.0;
      topP = 0.95;
      topK = 20;
      minP = 0.0;
      presencePenalty = 0.0;
      repetitionPenalty = 1.0;
    };
  };
  server = {
    host = "127.0.0.1";
    port = 11434;
    modelsMax = 1;
  };
  proxy.localPort = 11435;
}
