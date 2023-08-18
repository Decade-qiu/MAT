#ifndef MAT
#define MAT

#include <vector>
#include <immintrin.h>

#define FIELD_NUM 5
#define MAX_CHILD_NUM 512
#define MAX_BUCKET_NUM 8
#define MIN_PRIORITY INT32_MIN

enum {
    ACCEPT = 0,
    DROP,
    NAT,
    REJECT
};

enum {
    MASK = 0, RANGE
};

struct ip_field {
    unsigned int type;
    unsigned int value;
    unsigned int mask;
    unsigned int inv;
};

struct ip_key {
    unsigned int value;
    unsigned int mask;
};

struct ip_value {
    struct ip_field field[FIELD_NUM-1];
    int action;
    int priority;
    int id;
};

struct ip_rule{
    struct ip_key key;
    struct ip_value value;
};

struct slot{
    struct ip_key* key;
    struct ip_value* value;
    struct trie_node* node;
    unsigned int next;
    int used;
};

struct trie_node{
    struct ip_key* key;  
    struct ip_value* value;
    struct trie_node* childs[MAX_CHILD_NUM];
    int child_num = 0;
    unsigned int next;
    int layer;
    int index;
};

struct simd{
    __m256i keys, masks;
    int next_index[MAX_BUCKET_NUM];
    ip_value* values[MAX_BUCKET_NUM]; 
    struct trie_node* fa;
    int bucket_num;
};

struct packet{
    unsigned int src;
    unsigned int dst;
    unsigned short sport;
    unsigned short dport;
    unsigned char proto;
    unsigned short id;
    unsigned char tos;
};


// struct op_seq {
//     int layer;
//     int index;
//     unsigned int type;
//     struct ip_rule rule;
// };

int insert(struct ip_rule* rule);

int oracle(const struct packet* pkt);

int query(const struct packet* pkt);

void print_trie();

int init_MAT();

#endif
