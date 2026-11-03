#include <jni.h>
#include <algorithm>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "llama.h"

// Small CPU-only GGUF backend. No filesystem access outside the validated
// app-private model path supplied by SmallOfflineModel. No HTTP or telemetry.
namespace {
std::mutex gate;
llama_model * model = nullptr;
llama_context * context = nullptr;
bool backendReady = false;

void unload() {
    if (context) { llama_free(context); context = nullptr; }
    if (model) { llama_model_free(model); model = nullptr; }
}

void batch_add(llama_batch & batch, int offset, llama_token token, int position, bool output) {
    batch.token[offset] = token;
    batch.pos[offset] = position;
    batch.n_seq_id[offset] = 1;
    batch.seq_id[offset][0] = 0;
    batch.logits[offset] = output ? 1 : 0;
}

std::string trim_response(const std::string & input) {
    // Qwen3 may print an optional thinking section. This UI only displays
    // the final response; never show its internal reasoning.
    std::string s = input;
    auto endThink = s.find("</think>");
    if (endThink != std::string::npos) s.erase(0, endThink + 8);
    auto beginThink = s.find("<think>");
    if (beginThink != std::string::npos) s.erase(beginThink);
    const char* markers[] = {"<|im_end|>", "<|endoftext|>", "<|im_start|>"};
    for (const auto *marker : markers) {
        auto pos = s.find(marker);
        if (pos != std::string::npos) s.erase(pos);
    }
    const auto first = s.find_first_not_of(" \n\r\t");
    if (first == std::string::npos) return {};
    const auto last = s.find_last_not_of(" \n\r\t");
    return s.substr(first, last-first+1);
}
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_mediagenda_app_SmallOfflineModel_nativeLoadModel(
    JNIEnv *env, jobject, jstring jpath
) {
    std::lock_guard<std::mutex> lock(gate);
    if (model && context) return JNI_TRUE;
    unload();
    if (!backendReady) { llama_backend_init(); backendReady = true; }

    const char* cpath = env->GetStringUTFChars(jpath, nullptr);
    if (!cpath) return JNI_FALSE;
    const std::string path(cpath);
    env->ReleaseStringUTFChars(jpath, cpath);

    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = 0;
    model = llama_model_load_from_file(path.c_str(), mp);
    if (!model) { unload(); return JNI_FALSE; }

    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = 2048;
    cp.n_batch = 256;
    cp.n_ubatch = 128;
    cp.n_threads = std::max(2u, std::min(4u, std::thread::hardware_concurrency()));
    cp.n_threads_batch = cp.n_threads;
    context = llama_init_from_model(model, cp);
    if (!context) { unload(); return JNI_FALSE; }
    return JNI_TRUE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_mediagenda_app_SmallOfflineModel_nativeGenerate(
    JNIEnv *env, jobject, jstring jquestion, jint jmaxTokens
) {
    std::lock_guard<std::mutex> lock(gate);
    if (!model || !context) return env->NewStringUTF("");

    const char* cq = env->GetStringUTFChars(jquestion, nullptr);
    if (!cq) return env->NewStringUTF("");
    std::string question(cq);
    env->ReleaseStringUTFChars(jquestion, cq);
    if (question.size() > 3200) question.resize(3200);
    const int maxTokens = std::max(1, std::min(160, (int)jmaxTokens));

    // On-device ONLY; strictly no patient records are appended.
    const std::string prompt =
        "<|im_start|>system\n"
        "És o assistente simples da app SaúdePrática. Responde em português de "
        "Portugal, de forma clara e breve. Não inventes dados sobre a app. "
        "Não faças diagnósticos, não recomendes mudanças de medicação, "
        "tratamentos nem doses. Para alterar registos, exige sempre confirmação "
        "do utilizador na ficha nativa. Responde sem mostrar raciocínio interno. "
        "/no_think\n<|im_end|>\n<|im_start|>user\n"
        + question +
        "\n/no_think<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n";

    const llama_vocab * vocab = llama_model_get_vocab(model);
    const int required = -llama_tokenize(vocab, prompt.c_str(), prompt.size(), nullptr, 0, true, true);
    if (required <= 0 || required > (2048 - maxTokens - 16)) {
        return env->NewStringUTF("A pergunta é demasiado longa para este modelo.");
    }
    std::vector<llama_token> tokens(required);
    if (llama_tokenize(vocab, prompt.c_str(), prompt.size(), tokens.data(),
                       (int)tokens.size(), true, true) < 0) {
        return env->NewStringUTF("");
    }

    llama_memory_clear(llama_get_memory(context), false);
    llama_batch batch = llama_batch_init(256, 0, 1);
    if (!batch.token) return env->NewStringUTF("");
    auto sampler = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(sampler, llama_sampler_init_greedy());

    std::string answer;
    bool ok = true;
    int position = 0;

    // Prompt prefill in memory-bounded 256-token blocks.
    for (int offset=0; offset<required; offset+=256) {
        const int n = std::min(256, required-offset);
        batch.n_tokens = n;
        for (int i=0; i<n; ++i) {
            batch_add(batch, i, tokens[offset+i], position+i,
                      (offset+i == required-1));
        }
        if (llama_process(context, LLAMA_PROCESS_TYPE_DECODE, batch) != 0) {
            ok = false; break;
        }
        position += n;
    }
    if (ok) {
        for (int i=0; i<maxTokens; ++i) {
            const llama_token token = llama_sampler_sample(sampler, context, -1);
            if (llama_vocab_is_eog(vocab, token)) break;
            char piece[1024];
            const int n = llama_token_to_piece(vocab, token, piece, sizeof(piece), 0, true);
            if (n < 0 || n >= (int)sizeof(piece)) { ok = false; break; }
            answer.append(piece, n);
            if (answer.find("<|im_end|>") != std::string::npos) break;
            batch.n_tokens = 1;
            batch_add(batch, 0, token, position++, true);
            if (llama_process(context, LLAMA_PROCESS_TYPE_DECODE, batch) != 0) {
                ok = false; break;
            }
        }
    }
    llama_sampler_free(sampler);
    llama_batch_free(batch);
    if (!ok) return env->NewStringUTF("");
    return env->NewStringUTF(trim_response(answer).c_str());
}

extern "C" JNIEXPORT void JNICALL
Java_com_mediagenda_app_SmallOfflineModel_nativeUnloadModel(
    JNIEnv *, jobject
) {
    std::lock_guard<std::mutex> lock(gate);
    unload();
}
