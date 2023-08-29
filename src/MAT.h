#ifndef MAT
#define MAT

#include <immintrin.h>

#define FIELD_NUM 5
#define MAX_CHILD_NUM 512
#define MAX_ACCELERATE_DEPTH 12
#define MAX_BUCKET_NUM MAX_ACCELERATE_DEPTH
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
    int depth;
    struct trie_node* path[MAX_ACCELERATE_DEPTH];
    int path_num = 0;
    trie_node* father;
};

struct simd{
    __m256i key[2], mask[2];
    trie_node* buckets[MAX_BUCKET_NUM];
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

void print_info();

int init_MAT();

int delete_MAT();

#endif
