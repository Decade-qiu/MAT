#include "./src/MAT.h"
#include <fstream> 
#include <iostream>
#include <regex>

#define MAX_RULE 12000
#define MAX_PACKET 100000

std::vector<std::string> split(const std::string& str, const std::string& pattern);

void tuple2rule(std::vector<std::string> tuple, ip_rule* rule);

void tuple2packet(std::vector<std::string> tuple, packet* pkt);

struct ip_rule rule_set[MAX_RULE];
int rule_num = 0;

struct packet packet_set[MAX_PACKET];
int packet_num = 0;

void query_packets(char* file){
    std::ifstream inputFile(file); 
    if (!inputFile.is_open()) {
        printf("Error opening file %s.\n", file);
    }
    std::string line = "1";
    while (std::getline(inputFile, line)){
        std::vector<std::string> tuple = split(line, "\\s+");
        if (tuple.size() < 7) continue;
        tuple2packet(tuple, &packet_set[packet_num++]);
    }

    printf("Start query packets.\n");
    int i = 0, error_match = 0;
    for (i = 0; i < packet_num; i++){
        int rule_id = query(&packet_set[i]);
        if (rule_id != packet_set[i].id){
            error_match++;
            printf("Packet %d error match, rule id %d should be %d.\n", i, rule_id, packet_set[i].id);
        }
    }
    printf("Query %d packets, %d error match!\n", packet_num, error_match);
}

void insert_rule(char* file){
    std::ifstream inputFile;
    inputFile.open(file, std::ios::in);
    if (!inputFile.is_open()) {
        printf("Error opening file %s.\n", file);
        return;
    }
    std::string line = "1";
    while (std::getline(inputFile, line)){
        std::vector<std::string> tuple = split(line, "\\s+");
        if (tuple.size() < 9) continue;
        // printf("%s\n", line.c_str());
        tuple2rule(tuple, &rule_set[rule_num++]);
    }
    inputFile.close();

    printf("Start insert rules.\n");
    int i = 0, sucess_count = 0; 
    for (i = 0; i < rule_num; i++){
        int st = insert(&rule_set[i]);
        if (st == 0) sucess_count++; 
    }
    printf("Insert %d rules, %d sucess!\n", rule_num, sucess_count);
}

int main(int argc, char* argv[]){
    // if (argc != 3) {
    //     printf("Usage: %s rule_file_path packet_file_path", argv[0]);
    //     return 1;
    // }
    char* x = "../data/rules";
    char* y = "../data/packets";

    init_MAT();
    
    insert_rule(x);

    query_packets(y);
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

// tuple format:
// src/mask dst/mask proto sport dport pinv sinv dinv priority(id)
void tuple2rule(std::vector<std::string> tuple, struct ip_rule* rule){
    // src
    std::vector<std::string> src_mask = split(tuple[0], "/");
    std::vector<std::string> dst_mask = split(tuple[1], "/");
    rule->key.value = (unsigned int)std::stoll(src_mask[0]);
    rule->key.mask = (unsigned int)std::stoll(src_mask[1]);
    // dst
    rule->value.field[0].value = (unsigned int)std::stoll(dst_mask[0]);
    rule->value.field[0].mask = (unsigned int)std::stoll(dst_mask[1]);
    rule->value.field[0].type = MASK;
    // protcol
    rule->value.field[1].value = (unsigned int)std::stoll(tuple[2]);
    rule->value.field[1].mask = 0xff;
    rule->value.field[1].type = MASK;
    if (std::stoi(tuple[5]) == 1) rule->value.field[1].inv = 1;
    // sport
    std::vector<std::string> sport_mask = split(tuple[3], ":");
    rule->value.field[2].value = (unsigned int)std::stoll(sport_mask[0]);
    rule->value.field[2].mask = (unsigned int)std::stoll(sport_mask[1]);
    rule->value.field[2].type = RANGE;
    if (std::stoi(tuple[6]) == 1) rule->value.field[2].inv = 1;
    // dport
    std::vector<std::string> dport_mask = split(tuple[4], ":");
    rule->value.field[3].value = (unsigned int)std::stoll(dport_mask[0]);
    rule->value.field[3].mask = (unsigned int)std::stoll(dport_mask[1]);
    rule->value.field[3].type = RANGE;
    if (std::stoi(tuple[7]) == 1) rule->value.field[3].inv = 1;
    // priority (1 > 2 > 3 > ...)
    rule->value.priority = -std::stoi(tuple[8]);
    // id
    rule->value.id = rule_num;
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