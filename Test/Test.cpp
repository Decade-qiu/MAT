#include <immintrin.h>
#include <iostream>
#define u32 unsigned int

// __m256i simd_match(unsigned int t, __m256i value, __m256i mask, __m256i inv){
//     __m256i res = _mm256_setzero_si256();
//     __m256i tmp = _mm256_setzero_si256();
//     __m256i key = _mm256_set1_epi32(t);
//     tmp = _mm256_and_si256(key, mask);
//     res = _mm256_cmpeq_epi32(tmp, value);
//     unsigned int matchResults[8];
//     _mm256_storeu_si256((__m256i*)matchResults, res);
//     for (int i = 0;i < 8;i++){
//         printf("%08X ", matchResults[i]);
//     }printf("\n");
//     return res;
// }
const int N = 1000000;
int a[N];
int main() {
    // uint32_t v1 = 0xF0A80000, m1 = 0xFFFF0000;
    // uint32_t v2 = 0xF0A90000, m2 = 0xFFFF0000;
    // uint32_t v3 = 0xF0AA0000, m3 = 0xFFFF0000;
    // uint32_t v4 = 0xF0AB0000, m4 = 0xFFFF0000;
    // uint32_t values[8] = {v1, v2, v3, v4, 0, 0, 0, 0};
    // uint32_t masks[8] = {m1, m2, m3, m4, 0, 0, 0, 0};
    // __m256i value = _mm256_loadu_si256((__m256i*)values);
    // __m256i mask = _mm256_loadu_si256((__m256i*)masks);
    // __m256i inv = _mm256_setzero_si256();

    // __m256i res = simd_match(0xF0A90000, value, mask, inv);

    
    // unsigned int x = 0xC0000000;  // 要插入的值
    // __m256i simdMasks = _mm256_set_epi32(0, 0, 0, 0, 0, 0, 0, 10);  // 创建一个全部为零的寄存器

    // // 使用 _mm256_insert_epi32 将 x 插入到 simdMasks 中的第二个位置
    // __m256i blend_mask = _mm256_cmpgt_epi32(_mm256_set_epi32(7, 6, 5, 4, 3, 2, 1, 0), _mm256_set1_epi32(0));
    
    // simdMasks = _mm256_blend_epi32(simdMasks, _mm256_set1_epi32(x), 1<<1);
    
    // // 将结果取回到一个整数数组
    // unsigned int resultArray[8];
    // _mm256_storeu_si256((__m256i*)resultArray, simdMasks);

    // // 打印结果
    // for (int i = 0; i < 8; ++i) {
    //     printf("%08X ", resultArray[i]);
    // }
    // printf("\n");
    int ans = 0;
    for (int i = 0;i < N;i++){
        a[i] = i;
        ans += a[i];
    }
    return 0;
}
