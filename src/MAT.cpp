#include <stdio.h>
#include <stdlib.h>
#include <unordered_set>
#include <cstdlib> 
#include <ctime>  

#include "MAT.h"
#include "../utils/murmurhash.h"

#define SEED 13
#define MAX_ZERO_RULE_NUM 1024
#define MAX_LAYER_NUM 1024
#define MAX_SLOT_NUM 1024

unsigned int seed[MAX_LAYER_NUM];

struct ip_rule* Zc[MAX_ZERO_RULE_NUM];
int zero_rule_num = 0;

struct slot Sc[MAX_LAYER_NUM][MAX_SLOT_NUM];

struct trie_node* root;

void init_tree_node(struct trie_node* node, struct ip_rule* rule){
    node->key = &rule->key;
    node->value = &rule->value;
    node->next = 0;
    node->layer = 0;
    node->index = 0;
    node->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        node->childs[i] = nullptr;
    }
}

void init_vtree_node(struct trie_node* node, unsigned int key, unsigned int mask){
    node->key = (struct ip_key*)malloc(sizeof(struct ip_key));
    node->key->value = key & mask;
    node->key->mask = mask;
    node->value = (struct ip_value*)malloc(sizeof(struct ip_value));
    node->value->action = -1;
    node->next = 0;
    node->layer = 0;
    node->index = 0;
    node->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        node->childs[i] = nullptr;
    }
}

int store(int layer, struct trie_node* node, unsigned int mask){
    if (layer <= MAX_LAYER_NUM){
        uint32_t hash_key = (node->key->value & mask) ^ seed[layer-1], slot_index = 0;
        MurmurHash3_x86_32((uint32_t *)&hash_key, SEED, &slot_index);
        int index = (slot_index % MAX_SLOT_NUM) + 1;

        while (layer <= MAX_LAYER_NUM){
            struct slot* slot = &Sc[layer-1][index-1];
            if (slot->used==0 || (node->value->action == -1 && slot->key->value==node->key->value && slot->key->mask==mask)){
                slot->key = node->key;
                slot->value = node->value;
                slot->next = node->next;
                slot->used = 1;
                node->layer = layer;
                node->index = index;
                return 0;
            }
            layer++;
        }
    }
    node->layer = -1;
    return 0;
}

int write_node(struct trie_node* fa, std::vector<struct trie_node*>& childs, unsigned int mask){
    fa->next = mask;
    for (struct trie_node* child : childs){
        if (fa->child_num >= MAX_CHILD_NUM){
            printf("Error: too many childs exceed %d.\n", MAX_CHILD_NUM);
            return -1;
        }
        fa->childs[fa->child_num++] = child;
    }

    int i = 0, n = childs.size(), j = 0;
    if (fa->layer == -1){
        for (i = 0;i < n;i++) childs[i]->layer = -1;
        return 0;
    }

    if (fa->layer >= 1) Sc[fa->layer-1][fa->index-1].next = mask;
    std::vector<std::vector<trie_node*>> child_pair;
    for (i = 0;i < n;i++){
        child_pair.push_back({fa, childs[i]});
    }
    for (i = 0;i < n;i++){
        std::vector<trie_node*> cp = child_pair[i];
        trie_node* father = cp[0];
        trie_node* children = cp[1];
        store(father->layer+1, children, father->next);
        for (j = 0;j < children->child_num;j++){
            child_pair.push_back({children, children->childs[j]});
        }
        n = child_pair.size();
    }
    return 0;
}

int delete_node(struct trie_node *fa){
    if (fa->layer == -1) return 0;
    if (fa->layer >= 1) Sc[fa->layer-1][fa->index-1].next = 0;
    int i = 0, n = fa->child_num, j = 0;
    std::vector<trie_node*> child_pair;
    for (i = 0;i < n;i++){
        child_pair.push_back(fa->childs[i]);
    }
    for (i = 0;i < n;i++){
        trie_node* children = child_pair[i];
        if (children->layer == -1) continue;
        Sc[children->layer-1][children->index-1].used = 0;
        for (j = 0;j < children->child_num;j++){
            child_pair.push_back(children->childs[j]);
        }
        n = child_pair.size();
    }
    return 0;
}

int insert_tree(struct ip_rule* rule){
    struct trie_node* rn;
    rn = (struct trie_node *)malloc(sizeof(struct trie_node));
    init_tree_node(rn, rule); 

    unsigned int key = rule->key.value, imask = rule->key.mask;
    struct trie_node* cn = root;
    unsigned int cmask = cn->next;

    int i = 0, n = cn->child_num;
    for (i = 0;i < n;i++){
        struct trie_node* cur = cn->childs[i];
        if (cur->value->action == -1 && cur->key->value == key && cmask == imask){
            free(cur->key);
            free(cur->value);
            cur->key = &rule->key;
            cur->value = &rule->value;
            store(cn->layer+1, cur, cmask);
            break;
        }
        if (imask >= cmask && (key & cmask) == cur->key->value){
            cn = cur;
            cmask = cn->next;
            i = -1, n = cn->child_num;
        }
    }
    std::vector<struct trie_node*> insert_childs;
    if (cmask == 0 || cmask == imask){
        insert_childs.push_back(rn);
        write_node(cn, insert_childs, imask);
    }else if (imask > cmask){
        struct trie_node* vn;
        vn = (struct trie_node *)malloc(sizeof(struct trie_node));
        init_vtree_node(vn, key, cmask);
        insert_childs.push_back(vn);
        write_node(cn, insert_childs, cmask);
        insert_childs[0] = rn;
        write_node(vn, insert_childs, imask);
    }else{
        struct trie_node* vn;
        vn = (struct trie_node *)malloc(sizeof(struct trie_node));
        init_vtree_node(vn, cn->childs[0]->key->value, imask);
        delete_node(cn);
        std::vector<struct trie_node*> cchild;
        for (i = 0;i < cn->child_num;i++) cchild.push_back(cn->childs[i]);
        cn->child_num = 0;
        if (vn->key->value == key){
            insert_childs.push_back(rn);
            write_node(cn, insert_childs, imask);
            write_node(rn, cchild, cmask);
        }else{
            insert_childs.push_back(vn);
            write_node(cn, insert_childs, imask);
            write_node(vn, cchild, cmask);
            insert_childs[0] = rn;
            write_node(cn, insert_childs, imask);
        }
    }
    return 0;
}

int insert(struct ip_rule* rule){
    if (rule->key.mask == 0){
        Zc[zero_rule_num++] = rule;
        return 0;
    }
    int st = insert_tree(rule);
    return st;
}

int match(unsigned int t, ip_field* f){
    if (f->type == MASK){
        if ((t & f->mask) == f->value) return 1;
        return 0;
    }
    int flag_in = 0;
    if (t >= f->value && t <= f->mask) flag_in = 1;
    return flag_in ^ f->inv;
}

int value_match(const struct packet* pkt, struct ip_value* value){
    if (match(pkt->dst, &value->field[0]) &&
        match(pkt->proto, &value->field[1]) &&
        match(pkt->sport, &value->field[2]) &&
        match(pkt->dport, &value->field[3])){
        return 1;
        }
    return 0;
}

struct ip_value* zero_rule_query(const struct packet* pkt){
    int i = 0, res = -1, max_pri = MIN_PRIORITY;
    for (i = 0;i < zero_rule_num;i++){
        if (value_match(pkt, &Zc[i]->value)){
            if (Zc[i]->value.priority > max_pri){
                res = i;
                max_pri = Zc[i]->value.priority;
            }
        }
    }
    return res == -1 ? nullptr : &Zc[res]->value;
}

struct ip_value* oracle(const struct packet* pkt){
    ip_value* res = nullptr;
    int max_pri = MIN_PRIORITY;

    trie_node* cur = root;
    unsigned int cmask = cur->next, src = pkt->src;
    int i = 0, n = cur->child_num;
    while (i < n){
        trie_node* child = cur->childs[i];
        if (child->key->value == (src & cmask)){
            if (value_match(pkt, child->value)){
                if (child->value->priority > max_pri){
                    res = child->value;
                    max_pri = child->value->priority;
                }
            }
            cmask = child->next;
            if (cmask == 0){
                break;
            }else{
                cur = child;
                i = 0, n = child->child_num;
            }
        }else{
            i++;
        }
    }
    return res;
}

int query(const struct packet* pkt){
    ip_value* res = zero_rule_query(pkt);
    int max_pri = (res == nullptr ? MIN_PRIORITY : res->priority);

    unsigned int cmask = root->next, src = pkt->src;
    int oracle_flag = 0;
    uint32_t hash_key = (src & cmask) ^ seed[0], slot_index=0;
    MurmurHash3_x86_32((uint32_t *)&hash_key, SEED, &slot_index);
    int layer = 1, index = (slot_index % MAX_SLOT_NUM) + 1;
    while (layer <= MAX_LAYER_NUM){
        struct slot* cur = &Sc[layer-1][index-1];
        if (cur->used == 0) break;
        if (cur->key->value == (src & cmask)){
            if (value_match(pkt, cur->value)){
                if (cur->value->priority > max_pri){
                    max_pri = cur->value->priority;
                    res = cur->value;
                }
            }
            cmask = cur->next;
            if (cmask == 0){
                break;
            }else{
                layer++;
                if (layer <= MAX_LAYER_NUM){
                    hash_key = (src & cmask) ^ seed[layer-1];
                    MurmurHash3_x86_32((uint32_t *)&hash_key, SEED, &slot_index);
                    index = (slot_index % MAX_SLOT_NUM) + 1;
                }else{
                    oracle_flag = 1;
                }
            }
        }else{
            layer++;
            if (layer > MAX_LAYER_NUM) oracle_flag = 1;
        }
    }
    
    if (oracle_flag == 1){
        ip_value* oracle_res = oracle(pkt);
        if (oracle_res->priority > max_pri) res = oracle_res;
    }

    return res == nullptr ? 0 : res->id;
}

int init_MAT(){
    srand((int)time(0));
    std::unordered_set<int> seed_set;
    int index = 0;
    while (index != MAX_LAYER_NUM) {
        int cur = rand();
        if (seed_set.count(cur) == 0) {
            seed_set.insert(cur);
            seed[index++] = cur;
        }
    }

    root = (struct trie_node *)malloc(sizeof(struct trie_node));
    root->key = nullptr;
    root->value = nullptr;
    root->layer = 0;
    root->index = 0;
    root->next = 0;
    root->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        root->childs[i] = nullptr;
    }

    int i = 0, j = 0;
    for (i = 0;i < MAX_ZERO_RULE_NUM;i++){
        Zc[i] = nullptr;
    }

    for (i = 0;i < MAX_LAYER_NUM;i++){
        for (j = 0;j < MAX_SLOT_NUM;j++){
            Sc[i][j].used = 0;
            Sc[i][j].next = 0;
            Sc[i][j].key = nullptr;
            Sc[i][j].value = nullptr;
        }
    }
    printf("Init MAT sucess！\n");
    return 0;
}