#include <stdio.h>
#include <stdlib.h>
#include <unordered_set>
#include <unordered_map>
#include <queue>
#include <vector>
#include <fstream> 
#include <iostream>
#include <cstdlib> 
#include <cstring> 
#include <ctime>  
#include <algorithm>

#include "MAT.h"
#include "../utils/murmurhash.h"

#define SEED 31
#define MAX_ZERO_RULE_NUM 4096
#define MAX_LAYER_NUM 256
#define MAX_SLOT_NUM 128
#define QUICK_FIND_BIT 12
#define QUICK_FIND_MAX_NUM (1 << QUICK_FIND_BIT)

unsigned int seed[MAX_LAYER_NUM];
unsigned int hash_seed[MAX_SLOT_NUM];

struct simd acc[QUICK_FIND_MAX_NUM];

struct ip_rule* Zc[MAX_ZERO_RULE_NUM];
int zero_rule_num = 0;

std::unordered_set<struct trie_node*> Ec;

struct slot Sc[MAX_LAYER_NUM][MAX_SLOT_NUM];

struct trie_node* root;

void init_tree_node(struct trie_node* node, struct ip_rule* rule){
    node->key = &rule->key;
    node->value = &rule->value;
    node->next = 0;
    node->layer = 0;
    node->index = 0;
    node->depth = 0;
    node->father = nullptr;
    node->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        node->childs[i] = nullptr;
    }
    node->path_num = 0;
    for (int i = 0;i < MAX_ACCELERATE_DEPTH;i++){
        node->path[i] = nullptr;
    }
}

void init_vtree_node(struct trie_node* node, unsigned int key, unsigned int mask){
    node->key = (struct ip_key*)malloc(sizeof(struct ip_key));
    node->key->value = key & mask;
    node->key->mask = mask;
    node->value = (struct ip_value*)malloc(sizeof(struct ip_value));
    node->value->action = -1;
    node->value->id = node->value->priority = 0;
    node->next = 0;
    node->layer = 0;
    node->index = 0;
    node->depth = 0;
    node->father = nullptr;
    node->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        node->childs[i] = nullptr;
    }
    node->path_num = 0;
    for (int i = 0;i < MAX_ACCELERATE_DEPTH;i++){
        node->path[i] = nullptr;
    }
}

inline int slot_index(unsigned int hash_key){
    uint32_t index = 0;
    MurmurHash3_x86_32((uint32_t *)&hash_key, SEED, &index);
    return (index % MAX_SLOT_NUM) + 1;
}

inline int store(int layer, struct trie_node* node, unsigned int mask){
    if (layer <= MAX_LAYER_NUM && layer >= 1){
        uint32_t hash_key = (node->key->value & mask) ^ seed[layer-1]; 
        int index = slot_index(hash_key);
        while (layer <= MAX_LAYER_NUM){
            struct slot* slot = &Sc[layer-1][index-1];
            if (slot->used==0 || (slot->value->action == -1 && slot->key->value==node->key->value && slot->key->mask==mask)){
                if (slot->used != 0){
                    free(slot->key);
                    free(slot->value);
                }
                slot->key = node->key;
                slot->value = node->value;
                slot->next = node->next;
                slot->used = 1;
                slot->node = node;
                node->layer = layer;
                node->index = index;
                return 0;
            }
            layer++;
        }
    }
    node->layer = -1;
    Ec.insert(node);
    return 1;
}

// accelerate add
int write_acc(struct trie_node* cur, int start, int end){
    if (cur->depth > MAX_ACCELERATE_DEPTH) return 0;
    int quick_index = cur->key->value >> (32-QUICK_FIND_BIT);
    int i = 0, j = 0;
    for (i = 0;i < QUICK_FIND_MAX_NUM;i++){
        if ((quick_index & i) == quick_index){
            simd* acc_cur = &acc[i];
            if (acc_cur->bucket_num <= cur->path_num){
                for (j = start;j <= end;j++){
                    acc_cur->buckets[j] = cur->path[j];
                }
                acc_cur->bucket_num = cur->path_num;
            }
        }
    }
    return 0;
}

int write_node(struct trie_node* fa, std::vector<struct trie_node*>& childs, unsigned int mask){
    for (struct trie_node* child : childs){
        if (fa->child_num >= MAX_CHILD_NUM){
            printf("Error: too many childs exceed %d.\n", MAX_CHILD_NUM);
            return -1;
        }
        fa->childs[fa->child_num++] = child;
        child->father = fa;
    }

    fa->next = mask;
    if (fa->layer >= 1) Sc[fa->layer-1][fa->index-1].next = mask;
    int i = 0, n = childs.size(), j = 0;
    std::vector<std::vector<trie_node*>> child_pair;
    for (i = 0;i < n;i++){
        child_pair.push_back({fa, childs[i]});
    }
    for (i = 0;i < n;i++){
        std::vector<trie_node*> cp = child_pair[i];
        trie_node* father = cp[0];
        trie_node* children = cp[1];
        children->depth = father->depth+1;
        store(father->layer+1, children, father->next);
        for (j = 0;j < children->child_num;j++){
            child_pair.push_back({children, children->childs[j]});
        }
        n = child_pair.size();
    }
    return 0;
}

int dynamic_adjust(std::vector<std::vector<int>> layer_index){
    std::vector<trie_node*> adjust;
    int i = 0, n = layer_index.size();
    for (i = 0, n = layer_index.size();i < n;i++){
        int layer = layer_index[i][0], index = layer_index[i][1];
        for (;layer <= MAX_LAYER_NUM;layer++){
            struct slot* slot = &Sc[layer-1][index-1];
            if (slot->used != 1) continue;
            adjust.push_back(slot->node);
            std::vector<trie_node*> children = {slot->node};
            int j = 0, m = children.size();
            for (j = 0;j < m;j++){
                trie_node* child = children[j];
                if (child->layer >= 1){
                    layer_index.push_back({child->layer+1, child->index});
                    Sc[child->layer-1][child->index-1].used = 0;
                    Sc[child->layer-1][child->index-1].key = nullptr;
                    Sc[child->layer-1][child->index-1].value = nullptr;
                    Sc[child->layer-1][child->index-1].node = nullptr;
                    Sc[child->layer-1][child->index-1].next = 0;
                    child->layer = -1;
                    for (int k = 0;k < child->child_num;k++){
                        children.push_back(child->childs[k]);
                    }
                }
                m = children.size();
            }
        }
        n = layer_index.size();
    }
    for (trie_node* node : Ec) adjust.push_back(node);
    sort(adjust.begin(), adjust.end(), [](trie_node* a, trie_node* b){return a->depth < b->depth;});
    for (i = 0, n = adjust.size();i < n;i++){
        trie_node* cur = adjust[i];
        if (cur->layer != -1) continue;
        store(cur->father->layer+1, cur, cur->key->mask);
        std::vector<std::vector<trie_node*>> children;
        int j = 0, m = cur->child_num;
        for (j = 0;j < m;j++){
            children.push_back({cur, cur->childs[j]});
        }
        for (j = 0;j < m;j++){
            std::vector<trie_node*> cp = children[j];
            trie_node* father = cp[0];
            trie_node* child = cp[1];
            child->depth = father->depth+1;
            store(father->layer+1, child, father->next);
            for (int k = 0;k < child->child_num;k++){
                children.push_back({child, child->childs[k]});
            }
            m = children.size();
        }
    }
    std::unordered_set<trie_node *>::iterator it = Ec.begin();
    for (;it != Ec.end();) {
        if ((*it)->layer != -1) it = Ec.erase(it);
        else ++it;
    }
    return 0;
}

int dynamic_adjust2(std::unordered_map<int, int> index_layer){
    std::vector<trie_node*> adjust;
    std::vector<std::vector<int>> layer_index;
    for (std::pair<int, int> pair : index_layer){
        layer_index.push_back({pair.second, MAX_LAYER_NUM, pair.first});
    }
    int i = 0, n = layer_index.size();
    for (i = 0, n = layer_index.size();i < n;i++){
        int layer_start = layer_index[i][0], layer_end = layer_index[i][1];
        int layer = 0, index = layer_index[i][2];
        for (layer = layer_start;layer <= layer_end;layer++){
            struct slot* slot = &Sc[layer-1][index-1];
            if (slot->used == 0) continue;
            adjust.push_back(slot->node);
            std::vector<trie_node*> children = {slot->node};
            int j = 0, m = children.size();
            for (j = 0;j < m;j++){
                trie_node* child = children[j];
                if (child->layer >= 1){
                    if (index_layer.find(child->index) == index_layer.end()){
                        layer_index.push_back({child->layer+1, MAX_LAYER_NUM, child->index});
                        index_layer[child->index] = child->layer+1;
                    }else if (index_layer[child->index] > child->layer+1){
                        layer_index.push_back({child->layer+1, index_layer[child->index]-1, child->index});
                        index_layer[child->index] = child->layer+1;
                    }
                    Sc[child->layer-1][child->index-1].used = 0;
                    Sc[child->layer-1][child->index-1].key = nullptr;
                    Sc[child->layer-1][child->index-1].value = nullptr;
                    Sc[child->layer-1][child->index-1].node = nullptr;
                    Sc[child->layer-1][child->index-1].next = 0;
                    child->layer = -1;
                    for (int k = 0;k < child->child_num;k++){
                        children.push_back(child->childs[k]);
                    }
                }
                m = children.size();
            }
        }
        n = layer_index.size();
    }
    for (trie_node* node : Ec) adjust.push_back(node);
    sort(adjust.begin(), adjust.end(), [](trie_node* a, trie_node* b){return a->depth < b->depth;});
    for (i = 0, n = adjust.size();i < n;i++){
        trie_node* cur = adjust[i];
        if (cur->layer != -1) continue;
        store(cur->father->layer+1, cur, cur->key->mask);
        std::vector<std::vector<trie_node*>> children;
        int j = 0, m = cur->child_num;
        for (j = 0;j < m;j++){
            children.push_back({cur, cur->childs[j]});
        }
        for (j = 0;j < m;j++){
            std::vector<trie_node*> cp = children[j];
            trie_node* father = cp[0];
            trie_node* child = cp[1];
            child->depth = father->depth+1;
            store(father->layer+1, child, father->next);
            for (int k = 0;k < child->child_num;k++){
                children.push_back({child, child->childs[k]});
            }
            m = children.size();
        }
    }
    std::unordered_set<trie_node *>::iterator it = Ec.begin();
    for (;it != Ec.end();) {
        if ((*it)->layer != -1) it = Ec.erase(it);
        else ++it;
    }
    return 0;
}

int delete_node(struct trie_node *fa){
    if (fa->layer >= 1) Sc[fa->layer-1][fa->index-1].next = 0;
    int i = 0, n = fa->child_num, j = 0;
    fa->child_num = 0;
    std::vector<trie_node*> child_pair;
    for (i = 0;i < n;i++){
        child_pair.push_back(fa->childs[i]);
    }
    // std::vector<std::vector<int>> index_layer;
    std::unordered_map<int, int> index_layer2;
    for (i = 0;i < n;i++){
        trie_node* children = child_pair[i];
        if (children->layer >= 1){
            // index_layer.push_back({children->layer+1, children->index});
            if (index_layer2.find(children->index) == index_layer2.end()){
                index_layer2[children->index] = children->layer+1;
            }else{
                index_layer2[children->index] = std::min(index_layer2[children->index], children->layer+1);
            }
            Sc[children->layer-1][children->index-1].used = 0;
            Sc[children->layer-1][children->index-1].key = nullptr;
            Sc[children->layer-1][children->index-1].value = nullptr;
            Sc[children->layer-1][children->index-1].node = nullptr;
            Sc[children->layer-1][children->index-1].next = 0;
            children->layer = -1;
            for (j = 0;j < children->child_num;j++){
                child_pair.push_back(children->childs[j]);
            }
        }
        n = child_pair.size();
    }
    // dynamic_adjust(index_layer);    
    dynamic_adjust2(index_layer2);
    return 0;
}

int insert_path(std::vector<struct trie_node*> childs, trie_node* pre){
    int insert_idx = pre->depth-1;
    if (insert_idx >= MAX_ACCELERATE_DEPTH) return 1;
    int i = 0, n = childs.size(), j = 0;
    for (i = 0;i < n;i++){
        struct trie_node* cur = childs[i];
        // if (cur->depth > MAX_ACCELERATE_DEPTH) break;
        j = cur->path_num;
        if (j >= MAX_ACCELERATE_DEPTH) j--;
        for (;j > insert_idx;j--){
            cur->path[j] = cur->path[j-1];
        }
        cur->path[insert_idx] = pre;
        if (cur->path_num < MAX_ACCELERATE_DEPTH) cur->path_num++;
        write_acc(cur, 0, cur->path_num-1);
        for (j = 0;j < cur->child_num;j++){
            childs.push_back(cur->childs[j]);
        }
        n = childs.size();
    }
    return 0;
}

inline int record_path(trie_node* cur, trie_node* pre){
    if (cur->path_num >= MAX_ACCELERATE_DEPTH) return 1;
    cur->path[cur->path_num++] = pre;
    return 0;
}

inline int copy_node_path(trie_node* cur, trie_node* pre){
    int i = 0, n = pre->path_num;
    for (i = 0;i < n;i++){
        cur->path[i] = pre->path[i];
    }
    cur->path_num = n;
    return 0;
}

int insert_tree(struct ip_rule* rule){
    struct trie_node* rn;
    rn = (struct trie_node *)malloc(sizeof(struct trie_node));
    init_tree_node(rn, rule); 

    unsigned int key = rule->key.value, imask = rule->key.mask;
    struct trie_node* cn = root;
    unsigned int cmask = cn->next;

    int i = 0, n = cn->child_num, vn_eq_rn = 0;
    for (i = 0;i < n;i++){
        struct trie_node* cur = cn->childs[i];
        if (cur->value->action == -1 && cur->key->value == key && cmask == imask){
            cur->key = &rule->key;
            cur->value = &rule->value;
            int layer = cur->layer, index = cur->index;
            if (layer == -1) return 0;
            struct slot* slot = &Sc[layer-1][index-1];
            slot->key = &rule->key;
            slot->value = &rule->value;
            return 0;
        }
        // imask >= cmask && (key & cmask) == cur->key->value
        if ((imask & cmask) == cmask && (key & cmask) == cur->key->value){
            cn = cur;
            cmask = cn->next;
            i = -1, n = cn->child_num;
            record_path(rn, cn);
        }
    }
    std::vector<struct trie_node*> insert_childs;
    if (cmask == 0 || cmask == imask){
        insert_childs.push_back(rn);
        write_node(cn, insert_childs, imask);
        record_path(rn, rn);
        write_acc(rn, 0, rn->path_num-1);
    }else if ((imask & cmask) == cmask){
        struct trie_node* vn;
        vn = (struct trie_node *)malloc(sizeof(struct trie_node));
        init_vtree_node(vn, key, cmask);
        insert_childs.push_back(vn);
        write_node(cn, insert_childs, cmask);
        copy_node_path(vn, rn);
        record_path(vn, vn);
        write_acc(vn, 0, vn->path_num-1);
        insert_childs[0] = rn;
        write_node(vn, insert_childs, imask);
        record_path(rn, vn);
        record_path(rn, rn);
        write_acc(rn, 0, rn->path_num-1);
    }else{
        std::unordered_map<unsigned int, std::vector<struct trie_node*>> v_child;
        for (i = 0;i < cn->child_num;i++){
            unsigned int next_v_key = cn->childs[i]->key->value & imask;
            v_child[next_v_key].push_back(cn->childs[i]);
        }
        delete_node(cn);    
        for (std::pair<unsigned int, std::vector<trie_node *>> pair: v_child){
            unsigned int v_key = pair.first;
            std::vector<struct trie_node*> v_childs = pair.second;
            struct trie_node* vn;
            if (v_key == key){
                vn_eq_rn = 1;
                continue;
            }else{
                vn = (struct trie_node *)malloc(sizeof(struct trie_node));
                init_vtree_node(vn, v_key, imask);
            }
            insert_childs.clear();
            insert_childs.push_back(vn);
            write_node(cn, insert_childs, imask);
            copy_node_path(vn, rn);
            record_path(vn, vn);
            write_acc(vn, 0, vn->path_num-1);
            write_node(vn, v_childs, cmask);
            insert_path(v_childs, vn);
        }
        insert_childs.clear();
        insert_childs.push_back(rn);
        write_node(cn, insert_childs, imask);
        record_path(rn, rn);
        write_acc(rn, 0, rn->path_num-1);
        if (vn_eq_rn == 1){
            std::vector<struct trie_node*> v_childs = v_child[key];
            write_node(rn, v_childs, cmask);
            insert_path(v_childs, rn);
        }
    }
    return 0;
}

int insert(struct ip_rule* rule){
    if (rule->key.mask == 0){
        if (zero_rule_num >= MAX_ZERO_RULE_NUM || zero_rule_num < 0){
            printf("Error: too many zero rules exceed %d.\n", MAX_ZERO_RULE_NUM);
            return -1;
        }
        Zc[zero_rule_num++] = rule;
        return 0;
    }
    int st = insert_tree(rule); 
    return st; 
}

inline int match(unsigned int t, ip_field* f){
    if (f->type == MASK){
        if ((t & f->mask) == f->value) return 1 ^ f->inv;
        return 0 ^ f->inv;
    }
    int flag_in = 0;
    if (t >= f->value && t <= f->mask) flag_in = 1;
    return flag_in ^ f->inv;
}

inline int value_match(const struct packet* pkt, struct ip_value* value){
    if (match(pkt->dst, &value->field[0]) &&
        match(pkt->proto, &value->field[1]) &&
        match(pkt->sport, &value->field[2]) &&
        match(pkt->dport, &value->field[3])){
        return 1;
        }
    return 0;
}

inline struct ip_value* zero_rule_query(const struct packet* pkt){
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

inline struct ip_value* _oracle(const struct packet* pkt, struct trie_node* root){
    ip_value* res = nullptr;
    int max_pri = MIN_PRIORITY;

    trie_node* cur = root;
    unsigned int cmask = cur->next, src = pkt->src;
    int i = 0, n = cur->child_num;
    while (i < n){
        trie_node* child = cur->childs[i];
        if (child->key->value == (src & cmask)){
            if (child->value->action != -1 && value_match(pkt, child->value)){
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

// int simd_mask(unsigned int t, simd* cur){
//     __m256i value = cur->keys;
//     __m256i mask = cur->masks;
//     __m256i res = _mm256_setzero_si256();
//     __m256i key = _mm256_set1_epi32(t);
//     key = _mm256_and_si256(key, mask);
//     res = _mm256_cmpeq_epi32(key, value);
//     unsigned int matchResults[8];
//     _mm256_storeu_si256((__m256i*)matchResults, res);
//     for (int i = 0;i < cur->bucket_num;i++){
//         if (matchResults[i] == 0xFFFFFFFF) return i;
//     }
//     return -1;
// }

trie_node* accelerate(const struct packet* pkt, ip_value** res, int* max_pri){
    int quick_index = pkt->src >> (32-QUICK_FIND_BIT);
    simd* cur = &acc[quick_index];
    int i = 0;
    trie_node* next = root;
    for (i = 0;i < cur->bucket_num;i++){
        trie_node* node = cur->buckets[i];
        if ((pkt->src & node->key->mask) == node->key->value){
            if (node->value->action != -1 && value_match(pkt, node->value)){
                if (node->value->priority > *max_pri){
                    *max_pri = node->value->priority;
                    *res = node->value;
                }
            }
            if (next->depth < node->depth) next = node;
        }
    }
    return next;
}   

int query(const struct packet* pkt){
    // stage 1
    ip_value* res = zero_rule_query(pkt);
    int max_pri = (res == nullptr ? MIN_PRIORITY : res->priority);
    int oracle_flag = 0;
    // stage 2
    trie_node* pre = root;
    pre = accelerate(pkt, &res, &max_pri);
    // stage 3
    unsigned int cmask = pre->next, src = pkt->src;
    uint32_t hash_key = (src & cmask) ^ seed[pre->layer];
    int layer = pre->layer+1, index = slot_index(hash_key);
    if (pre->layer == -1) oracle_flag = 1;
    while (layer <= MAX_LAYER_NUM){
        struct slot* cur = &Sc[layer-1][index-1];
        if (cur->used == 0) { 
            break;
        }
        if (cur->key->value == (src & cmask)){
            if (cur->value->action >= 0 && value_match(pkt, cur->value)){
                if (cur->value->priority > max_pri){
                    max_pri = cur->value->priority;
                    res = cur->value;
                }
            }
            pre = cur->node;
            cmask = cur->next;
            if (cmask == 0){
                break;
            }else{
                layer++;
                if (layer <= MAX_LAYER_NUM){
                    hash_key = (src & cmask) ^ seed[layer-1];
                    index = slot_index(hash_key);
                }else{
                    oracle_flag = 1;
                }
            }
        }else{
            layer++;
            if (layer > MAX_LAYER_NUM) oracle_flag = 1;
        }
    }
    // stage 4
    // oracle_flag = 0;
    if (oracle_flag == 1){
        ip_value* oracle_res = _oracle(pkt, pre);
        if (oracle_res!=nullptr && oracle_res->priority > max_pri) res = oracle_res;
    }
    return res == nullptr ? 0 : res->id;
}

int oracle(const struct packet* pkt){
    ip_value* res = zero_rule_query(pkt);
    int max_pri = (res == nullptr ? MIN_PRIORITY : res->priority);
    ip_value* oracle_res = _oracle(pkt, root);
    if (oracle_res!=nullptr && oracle_res->priority > max_pri) res = oracle_res;
    return res == nullptr ? 0 : res->id;
}

void gen_seed(){
    srand((int)time(0));
    std::unordered_set<int> seed_set;
    int index = 0;
    // while (index != MAX_SLOT_NUM) {
    //     int cur = rand();
    //     if (seed_set.count(cur) == 0) {
    //         seed_set.insert(cur);
    //         hash_seed[index++] = cur;
    //     }
    // }
    // std::ifstream fin;
    // fin.open("../data/seed", std::ios::in);
    // for (int i = 0;i < MAX_LAYER_NUM;i++) fin >> seed[i];
    seed_set.clear();
    index = 0;
    while (index != MAX_LAYER_NUM) {
        int cur = rand();
        if (seed_set.count(cur) == 0) {
            seed_set.insert(cur);
            seed[index++] = cur;
        }
    }
    std::ofstream fout;
    fout.open("../data/seed");
    for (int i = 0;i < MAX_LAYER_NUM;i++) fout << seed[i] << "\n";
}

void init_root(){
    root = (struct trie_node *)malloc(sizeof(struct trie_node));
    root->key = nullptr;
    root->value = nullptr;
    root->layer = 0;
    root->index = 0;
    root->father = nullptr;
    root->depth = 0;
    root->next = 0;
    root->child_num = 0;
    for (int i = 0;i < MAX_CHILD_NUM;i++){
        root->childs[i] = nullptr;
    }
    root->path_num = 0;
    for (int i = 0;i < MAX_ACCELERATE_DEPTH;i++){
        root->path[i] = nullptr;
    }
}

void init_data_struct(){
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
            Sc[i][j].node = nullptr;
        }
    }
    for (i = 0;i < QUICK_FIND_MAX_NUM;i++){
        acc[i].bucket_num = 0;
        for (j = 0;j < MAX_BUCKET_NUM;j++){
            acc[i].buckets[j] = nullptr;
        }
    }
}

int init_MAT(){
    gen_seed();

    init_root();

    init_data_struct();
    
    printf("Init MAT sucess！\n");
    return 0;
}

int countOnes(unsigned int n) {
    int count = 0;
    while (n != 0) {
        n = n & (n - 1);
        count++;
    }
    return count;
}

void print_acc(){
    if (root == nullptr) return;
    std::ofstream fout;
    fout.open("../data/acc");
    int i = 0, j = 0;
    for (i = 0;i < QUICK_FIND_MAX_NUM;i++){
        simd* cur = &acc[i];
        fout << cur->bucket_num << '\t';
        for (j = 0;j < cur->bucket_num;j++){
            fout << cur->buckets[j]->value->id << " ";
        }
        fout << '\n';
    }
    fout.close();
}

void display(trie_node* root){
    if (root == nullptr) return;
    std::ofstream fout;
    fout.open("../data/trie");
    // BFS
    int max_depth = 0, max_width = 0, max_child = 0, total_num = 0, outtable = 0;
    std::queue<struct trie_node*> q;
    q.push(root);
    while (!q.empty()){
        int s = q.size(), depth_err = 0;
        total_num += s;
        max_width = std::max(max_width, s);
        fout << max_depth << " " << s << " " << total_num << '\n';
        while (s--){
            trie_node* cur = q.front();
            q.pop();
            if (cur->layer == -1) outtable++;
            if (cur->layer >= 1){
                fout << std::hex << cur->key->value << "/" << std::dec << countOnes(cur->key->mask) << (cur->value->action==-1 ? "V " : " ") << cur->value->id << ' ' << cur->layer << "@" << cur->index << " " << cur->depth << " " << cur->path_num << "\n";
            }
            if (cur->depth != max_depth){
                depth_err = 1;
            }
            for (int i = 0;i < cur->child_num;i++){
                q.push(cur->childs[i]);
            }
            max_child = std::max(max_child, cur->child_num);
        }
        max_depth++;
        fout << (depth_err==1 ? "ERR" : "ACC") << '\n';
    }
    fout.close();
    printf("Trie: total %d, depth %d, width %d max_child %d (%d)\n", total_num, max_depth, max_width, max_child, outtable);
}

void print_Ec(){
    int j = Ec.size();
    printf("Ec: not_in_Sc_node_num %d\n", j);
}

void print_Sc(){
    std::ofstream fout;
    fout.open("../data/Sc");
    int i = 0, j = 0, k = 0, maxid = 0;
    for (i = 0;i < MAX_LAYER_NUM;i++){
        for (j = 0;j < MAX_SLOT_NUM;j++){
            if (Sc[i][j].used == 0) continue;
            if (Sc[i][j].node->father->layer+1 < i){
                int flag = 0;
                for (k = i-1;k >= Sc[i][j].node->father->layer+1;k--){
                    if (Sc[k][j].used == 0){
                        flag = 1;
                    }
                }
                if (flag == 0) continue;
                fout << i << "@" << j << " ";
                for (k = i;k >= Sc[i][j].node->father->layer+1;k--){
                    fout << Sc[k][j].used << "|";
                    if (Sc[k][j].used == 1){
                        maxid = std::max(maxid, Sc[k][j].value->id);
                        fout << Sc[k][j].value->id;
                    }
                    fout << " ";
                }
                fout << '\n';
            }
        }
    }
    fout << maxid << '\n';
    fout.close();
}

void print_info(){
    display(root);
    print_acc();
    print_Ec();
    print_Sc();
}