#include "./src/MAT.h"
#include <iostream>

int main(){
    // if (argc != 3) {
    //     printf("Usage: %s rule_file_path packet_file_path", argv[0]);
    //     return 1;
    // }
    std::string x = "../data/rules_", x1 = "../data/rules.bak";
    std::string y = "../data/packets_", y1 = "../data/packets.bak"; 
    for (int i = 1;i <= 11;i++){
        if (i == 11) i = 15;
        printf("====================Test %dk====================\n", i);

        read_data_set(x+std::to_string(i)+"k", y+std::to_string(i)+"k");

        init_MAT();
        
        insert_rule();

        print_info();

        query_packets();

        delete_MAT();
    }
}