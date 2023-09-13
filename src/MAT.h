#ifndef MAT
#define MAT

#include <string>
#include <immintrin.h>

#define MAX_RULE 60000
#define MAX_PACKET 100000

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
    MASK = 0, RANGE, EXACT
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
    int used;
    unsigned int next;
    struct ip_key* key;
    struct ip_value* value;
    struct trie_node* node;
};

struct trie_node{
    unsigned int next;
    struct ip_key* key;  
    struct ip_value* value;
    struct trie_node* childs[MAX_CHILD_NUM];
    int child_num = 0;
    int layer;
    int index;
    struct trie_node* path[MAX_ACCELERATE_DEPTH];
    int path_num = 0;
    trie_node* father;
    int depth;
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

void print_info(int scale);

int init_MAT();

int delete_MAT();

void read_data_set(std::string rule_file, std::string packet_file);

void query_packets();

void insert_rule();

#endif