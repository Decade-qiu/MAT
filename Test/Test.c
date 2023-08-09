#include <stdio.h>
#include <stdint.h>
#include <immintrin.h> // 使用AVX指令集

int main() {
    uint32_t v1 = 0xC0A80000, m1 = 0xFFFF0000;
    uint32_t v2 = 0xC0A90000, m2 = 0xFFFF0000;
    uint32_t v3 = 0xC0AA0000, m3 = 0xFFFF0000;
    uint32_t v4 = 0xC0AB0000, m4 = 0xFFFF0000;
    uint32_t your_key = 0xC0AA0011;

    uint32_t values[8] = {v1, v2, v3, v4, v1, v2, v3, v4};
    uint32_t masks[8] = {m1, m2, m3, m4, m1, m2, m3, m4};

    // Load key and masks into AVX registers
    __m256i simdKey = _mm256_set1_epi32(your_key);
    __m256i simdMasks = _mm256_loadu_si256((__m256i*)masks);
    __m256i simdValues = _mm256_loadu_si256((__m256i*)values);

    // Perform bitwise AND operation between key and mask using AVX intrinsics
    __m256i simdResult = _mm256_and_si256(simdKey, simdMasks);

    // Compare the result with values using SIMD equality comparison
    __m256i comparison = _mm256_cmpeq_epi32(simdResult, simdValues);

    // Store the AVX result back to the result array
    uint32_t matchResults[8], compareResults[8];
    _mm256_storeu_si256((__m256i*)matchResults, simdResult);
    _mm256_storeu_si256((__m256i*)compareResults, comparison);

    // Print the match results
    for (int i = 0; i < 8; ++i) {
        printf("Value %d: %X %X\n", i + 1, matchResults[i], compareResults[i]);
    }

    return 0;
}
