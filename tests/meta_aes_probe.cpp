// SPDX-License-Identifier: GPL-3.0-or-later
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sched.h>
#include <vector>
#include "crypto/randomx/aes_hash.hpp"

void hashAndFillAes1Rx4_VAES512(void*, size_t, void*, void*);
constexpr size_t pad_size = 2097152;
using Kernel = void (*)(void*, size_t, void*, void*);

static uint64_t next_random(uint64_t& state) {
    state ^= state >> 12;
    state ^= state << 25;
    state ^= state >> 27;
    return state * 2685821657736338717ULL;
}

static void* aligned_buffer(size_t size) {
    void* p = nullptr;
    if (posix_memalign(&p, 64, size)) std::abort();
    return p;
}

static double measure(Kernel kernel, void* pad, void* hash, void* state, size_t repeats) {
    for (size_t i = 0; i < 128; ++i) kernel(pad, pad_size, hash, state);
    const auto start = std::chrono::steady_clock::now();
    for (size_t i = 0; i < repeats; ++i) kernel(pad, pad_size, hash, state);
    const auto end = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::micro>(end - start).count() / repeats;
}

int main() {
    if (!__builtin_cpu_supports("aes") || !__builtin_cpu_supports("vaes") ||
        !__builtin_cpu_supports("avx512f")) {
        std::puts("Required AES/VAES/AVX-512F CPU support is unavailable");
        return 77;
    }
    cpu_set_t allowed;
    CPU_ZERO(&allowed);
    int pinned_cpu = -1;
    if (sched_getaffinity(0, sizeof(allowed), &allowed) == 0) {
        for (int cpu = 0; cpu < CPU_SETSIZE; ++cpu) {
            if (CPU_ISSET(cpu, &allowed)) {
                cpu_set_t chosen;
                CPU_ZERO(&chosen);
                CPU_SET(cpu, &chosen);
                if (sched_setaffinity(0, sizeof(chosen), &chosen) == 0) pinned_cpu = cpu;
                break;
            }
        }
    }
    auto* pad1 = static_cast<uint64_t*>(aligned_buffer(pad_size));
    auto* pad2 = static_cast<uint64_t*>(aligned_buffer(pad_size));
    alignas(64) uint64_t hash1[8], hash2[8], state1[8], state2[8];
    uint64_t random_state = 0x95cce349729f7af1ULL;
    constexpr size_t cases = 128;
    for (size_t test = 0; test < cases; ++test) {
        for (size_t i = 0; i < pad_size / sizeof(uint64_t); ++i) pad1[i] = next_random(random_state);
        for (auto& x : state1) x = next_random(random_state);
        std::memcpy(pad2, pad1, pad_size);
        std::memcpy(state2, state1, sizeof(state1));
        hashAndFillAes1Rx4<0, 2>(pad1, pad_size, hash1, state1);
        hashAndFillAes1Rx4_VAES512(pad2, pad_size, hash2, state2);
        if (std::memcmp(hash1, hash2, sizeof(hash1)) ||
            std::memcmp(state1, state2, sizeof(state1)) ||
            std::memcmp(pad1, pad2, pad_size)) {
            std::printf("Differential comparison failed on case %zu\n", test);
            return 1;
        }
    }
    constexpr size_t repeats = 2048;
    constexpr size_t rounds = 9;
    std::array<double, rounds> baseline, vaes;
    for (size_t round = 0; round < rounds; ++round) {
        if (round & 1) {
            vaes[round] = measure(hashAndFillAes1Rx4_VAES512, pad2, hash2, state2, repeats);
            baseline[round] = measure(hashAndFillAes1Rx4<0, 2>, pad1, hash1, state1, repeats);
        } else {
            baseline[round] = measure(hashAndFillAes1Rx4<0, 2>, pad1, hash1, state1, repeats);
            vaes[round] = measure(hashAndFillAes1Rx4_VAES512, pad2, hash2, state2, repeats);
        }
    }
    std::printf("{\"scratchpad_bytes\":%zu,\"differential_cases_passed\":%zu,\"pinned_cpu\":%d,\"repetitions_per_round\":%zu,\"rounds\":%zu,\"aes128_us\":[", pad_size, cases, pinned_cpu, repeats, rounds);
    for (size_t i = 0; i < rounds; ++i) std::printf("%s%.3f", i ? "," : "", baseline[i]);
    std::printf("],\"vaes512_us\":[");
    for (size_t i = 0; i < rounds; ++i) std::printf("%s%.3f", i ? "," : "", vaes[i]);
    std::printf("],");
    std::sort(baseline.begin(), baseline.end());
    std::sort(vaes.begin(), vaes.end());
    std::printf("\"median_aes128_us\":%.3f,\"median_vaes512_us\":%.3f,\"component_speedup_pct\":%.3f}\n", baseline[rounds / 2], vaes[rounds / 2], (baseline[rounds / 2] / vaes[rounds / 2] - 1) * 100);
    std::free(pad1);
    std::free(pad2);
}
