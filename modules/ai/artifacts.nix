{
  source = {
    repository = "https://github.com/ggml-org/llama.cpp.git";
    revision = "434ddbbc0e30522e897670681e503b797c12b7c1";
    grammarRepetitionThreshold = 20000;
    installPrefix = "/opt/llama-cpp-opencode";
  };
  defaultModel = "qwen3.6-35b-a3b-ud-q5-k-m";
  models."qwen3.6-35b-a3b-ud-q5-k-m" = {
    artifact = {
      id = "Qwen3.6-35B-A3B-GGUF:MXFP4_MOE";
      repository = "unsloth/Qwen3.6-35B-A3B-GGUF";
      revision = "a483e9e6cbd595906af30beda3187c2663a1118c";
      file = "Qwen3.6-35B-A3B-MXFP4_MOE.gguf";
      path = "/var/lib/llama/models/Qwen3.6-35B-A3B-MXFP4_MOE.gguf";
      sha256 = "2fdd20997c4d88ee25f70f500c61f8b999378d92ab055f9d450fc70d617158d3";
    };
    runtime = {
      contextSize = 65536;
      fitTarget = 6144;
      cacheTypeK = "q8_0";
      cacheTypeV = "q8_0";
      batchSize = 2048;
      microBatchSize = 512;
      parallel = 1;
      enableThinking = true;
      temperature = 0.6;
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
