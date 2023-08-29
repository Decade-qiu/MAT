#include "./src/MAT.h"
#include <fstream> 
#include <iostream>
#include <regex>
#include <random>

#define MAX_RULE 50000
#define MAX_PACKET 100000

struct ip_rule rule_set[MAX_RULE];
int rule_num = 0;

struct packet packet_set[MAX_PACKET];
int packet_num = 0;

std::vector<std::string> split(const std::string& str, const std::string& pattern);

void read_data_set(std::string rule_file, std::string packet_file);

template <typename T>
void uniform_shaflle(T* array, int size);

void tuple2rule(std::vector<std::string> tuple, ip_rule* rule);

void tuple2packet(std::vector<std::string> tuple, packet* pkt);

void query_packets(){
    // uniform_shaflle(packet_set, packet_num);

    printf("Start query packets.\n");
    double run_time = 0;
    int i = 0, error_match = 0;
    for (i = 0; i < packet_num; i++){
        clock_t start = clock();
        int rule_id = query(&packet_set[i]);
        clock_t end = clock();
        run_time += (double)(end - start) / CLOCKS_PER_SEC;
        if (rule_id != packet_set[i].id){
            error_match++;
            // printf("Error match: %d %d\n", rule_id, packet_set[i].id);
        }
    }
    printf("Query %d packets, %d error match, thoughout %.6f!\n", packet_num, error_match, packet_num / run_time);

    // printf("Start query packets.(only Oracle)\n");
    // run_time = 0;
    // i = 0, error_match = 0;
    // for (i = 0; i < packet_num; i++){
    //     clock_t start = clock();
    //     int rule_id = oracle(&packet_set[i]);
    //     clock_t end = clock();
    //     run_time += (double)(end - start) / CLOCKS_PER_SEC;
    //     if (rule_id != packet_set[i].id){
    //         error_match++;
    //         // printf("Error match: %d %d\n", rule_id, packet_set[i].id);
    //     }
    // }
    // printf("Query %d packets, %d error match, thoughout %.6f!\n", packet_num, error_match, packet_num / run_time);
}

void insert_rule(){
    uniform_shaflle(rule_set, rule_num);

    printf("Start insert rules.\n");
    double run_time = 0;
    int i = 0, sucess_count = 0; 
    for (i = 0; i < rule_num; i++){
        clock_t start = clock();
        int st = insert(&rule_set[i]);
        clock_t end = clock();
        run_time += (double)(end - start) / CLOCKS_PER_SEC;
        if (st == 0) sucess_count++; 
    }
    printf("Insert %d rules, %d sucess, thoughout %.6f!\n", rule_num, sucess_count, rule_num / run_time);
}

int main(int argc, char* argv[]){
    // if (argc != 3) {
    //     printf("Usage: %s rule_file_path packet_file_path", argv[0]);
    //     return 1;
    // }
    std::string x = "../data/rules_", x1 = "../data/rules.bak";
    std::string y = "../data/packets_", y1 = "../data/packets.bak"; 
    int tp[5] = {1, 3, 6, 10, 15};
    for (int i = 0;i < 5;i++){
        printf("====================Test %dk====================\n", tp[i]);

        read_data_set(x+std::to_string(tp[i])+"k", y+std::to_string(tp[i])+"k");

        init_MAT();
        
        insert_rule();

        print_info();

        query_packets();

        delete_MAT();
    }
}

// tuple format:
// src/mask dst/mask proto sport dport pinv sinv dinv priority(id)
void tuple2rule(std::vector<std::string> tuple, struct ip_rule* rule){
    // src
    std::vector<std::string> src_mask = split(tuple[0], "/");
    std::vector<std::string> dst_mask = split(tuple[1], "/");
    rule->key.value = (unsigned int)std::stoll(src_mask[0]);
    rule->key.mask = (unsigned int)std::stoll(src_mask[1]);
    rule->key.value &= rule->key.mask;
    // dst
    rule->value.field[0].value = (unsigned int)std::stoll(dst_mask[0]);
    rule->value.field[0].mask = (unsigned int)std::stoll(dst_mask[1]);
    rule->value.field[0].value &= rule->value.field[0].mask;
    rule->value.field[0].type = MASK;
    rule->value.field[0].inv = 0;
    // protcol
    rule->value.field[1].value = (unsigned int)std::stoll(tuple[2]);
    rule->value.field[1].mask = 0xff;
    rule->value.field[1].value &= rule->value.field[1].mask;
    rule->value.field[1].type = MASK;
    if (rule->value.field[1].value == 0) rule->value.field[1].mask = 0;
    if (std::stoi(tuple[5]) == 1) rule->value.field[1].inv = 1;
    else rule->value.field[1].inv = 0;
    // sport
    std::vector<std::string> sport_mask = split(tuple[3], ":");
    rule->value.field[2].value = (unsigned int)std::stoll(sport_mask[0]);
    rule->value.field[2].mask = (unsigned int)std::stoll(sport_mask[1]);
    rule->value.field[2].type = RANGE;
    if (std::stoi(tuple[6]) == 1) rule->value.field[2].inv = 1;
    else rule->value.field[2].inv = 0;
    // dport
    std::vector<std::string> dport_mask = split(tuple[4], ":");
    rule->value.field[3].value = (unsigned int)std::stoll(dport_mask[0]);
    rule->value.field[3].mask = (unsigned int)std::stoll(dport_mask[1]);
    rule->value.field[3].type = RANGE;
    if (std::stoi(tuple[7]) == 1) rule->value.field[3].inv = 1;
    else rule->value.field[3].inv = 0;
    // priority (1 > 2 > 3 > ...)
    rule->value.priority = -std::stoi(tuple[8]);
    // id
    rule->value.id = -rule->value.priority;
    // action
    rule->value.action = ACCEPT;
}

// packet format:
// ID=id src dst proto sport dport rule_id
// rule_id is the rule which the packet should match
void tuple2packet(std::vector<std::string> tuple, packet* pkt){
    // src
    pkt->src = (unsigned int)std::stoll(tuple[1]);
    // dst
    pkt->dst = (unsigned int)std::stoll(tuple[2]);
    // protcol
    pkt->proto = (unsigned char)std::stoi(tuple[3]);
    // sport
    pkt->sport = (unsigned short)std::stoi(tuple[4]);
    // dport
    pkt->dport = (unsigned short)std::stoi(tuple[5]);
    // rule_id
    pkt->id = (unsigned short)std::stoi(tuple[6]);
    // tos
    pkt->tos = 0xff;
}

void read_data_set(std::string rule_file, std::string packet_file){
    rule_num = packet_num = 0;
    std::ifstream inputFile;
    inputFile.open(rule_file, std::ios::in);
    if (!inputFile.is_open()) {
        printf("Error opening file %s.\n", rule_file);
        return;
    }else{
        std::string line = "1";
        while (std::getline(inputFile, line)){
            std::vector<std::string> tuple = split(line, "\\s+");
            if (line == "\n" || line == "\t\n" || tuple.size() < 9) break;
            tuple2rule(tuple, &rule_set[rule_num++]);
        }
        inputFile.close();
    }
    inputFile.open(packet_file, std::ios::in);
    if (!inputFile.is_open()) {
        printf("Error opening file %s.\n",packet_file);
        return;
    }else{
        std::string line = "1";
        while (std::getline(inputFile, line)){
            std::vector<std::string> tuple = split(line, "\\s+");
            if (line == "\n" || line == "\t\n" || tuple.size() < 7) break;
            tuple2packet(tuple, &packet_set[packet_num++]);
        }
    }
}

std::vector<std::string> split(const std::string& str, const std::string& pattern) {
    std::regex re(pattern);
    std::sregex_token_iterator it(str.begin(), str.end(), re, -1);
    std::sregex_token_iterator end;
    std::vector<std::string> tokens;
    for (; it != end; ++it) {
        tokens.push_back(*it);
    }
    return tokens;
}

template <typename T>
void uniform_shaflle(T* array, int size){
    std::random_device rd;
    std::mt19937 gen(rd());
    std::shuffle(array, array + size, gen);
}