#ifndef MAT
#define MAT

#include <vector>

#define FIELD_NUM 4
#define MAX_CHILD_NUM 1024
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
    struct ip_field field[FIELD_NUM];
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

int query(const struct packet* pkt);

void print_trie();

int init_MAT();

#endif
