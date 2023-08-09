#include <immintrin.h>
#include <iostream>
#define u32 unsigned int

int main() {
    u32 v1 = 0xC0A80000, m1 = 0xFFFF0000;
    u32 v2 = 0xC0A90000, m2 = 0xFFFF0000;
    u32 v3 = 0xC0AA0000, m3 = 0xFFFF0000;
    u32 v4 = 0xC0AB0000, m4 = 0xFFFF0000;
    u32 v5 = 0xC0AC0000, m5 = 0xFFFF0000;
    u32 your_key = 0xC0AA0011;

    uint32_t values[4] = {v1, v2, v3, v4};  // Replace v1, v2, v3, v4 with actual values
    uint32_t masks[4] = {m1, m2, m3, m4};  // Replace m1, m2, m3, m4 with actual masks

    // Load values and masks into SIMD registers
    __m128i simdValues = _mm_loadu_si128((const __m128i*)values);
    __m128i simdMasks = _mm_loadu_si128((const __m128i*)masks);

    // Perform bitwise AND operation between key and mask
    __m128i key = _mm_set1_epi32(your_key);  

    __m128i result = _mm_and_si128(key, simdMasks);

    // Compare the result with values using SIMD equality comparison
    __m128i comparison = _mm_cmpeq_epi32(result, simdValues);

    // Store the comparison results in an array
    uint32_t matchResults[4], compareResults[4];
    _mm_storeu_si128((__m128i*)matchResults, result);
    _mm_storeu_si128((__m128i*)compareResults, comparison);

    // Print the match results
    for (int i = 0; i < 4; ++i) {
        std::cout << "Value " << i + 1 << ": " << std::hex << matchResults[i] << " " << std::hex << compareResults[i] << std::endl;
    }

    return 0;
}
