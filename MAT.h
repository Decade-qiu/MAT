#ifndef MAT
#define MAT

#define FIELD_NUM 4

enum {
    ACCEPT,
    DROP,
    NAT,
    REJECT
};

enum {
    MASK, RANGE, EXACT 
};

struct ip_field {
    unsigned int type;
    unsigned int value;
    unsigned int mask;
    unsigned int inv;
};

struct ip_key {
    unsigned int type;
    unsigned int value;
    unsigned int mask;
};

struct ip_value {
    struct ip_field field[FIELD_NUM];
    unsigned int action;
    unsigned int priority;
};

struct ip_rule{
    struct ip_key key;
    struct ip_value value;
};

struct trie_node{
    struct ip_key key;
    struct ip_value value;
    unsigned int next;
    unsigned int layer;
    unsigned int index;
};

struct op_seq {
    unsigned int layer;
    unsigned int index;
    unsigned int type;
    struct ip_rule rule;
};

int insert(struct ip_rule rule);

int insert_tree(struct ip_rule rule);

int write_node(struct trie_node node, struct trie_node *childs, unsigned int prefix_len);

int delete_node(struct trie_node *node);

int store(struct trie_node node);

int update(struct ip_rule rule, struct slot liod);

int qurey(struct packet pkt);

int oracle(struct packet pkt);

#endif
