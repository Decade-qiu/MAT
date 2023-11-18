#include "./src/MAT.h"

int main(){
    // if (argc != 3) {
    //     printf("Usage: %s rule_file_path packet_file_path", argv[0]);
    //     return 1;
    // }
    std::string x = "../data/rules_", x1 = "../data/rules.bak";
    std::string y = "../data/packets_", y1 = "../data/packets.bak"; 
<<<<<<< HEAD
    int a[5] = {0, 1, 8, 15, 22};
    for (int i = 1;i <= 1;i++){
        int scale = i;
        if (i == 11) scale = 15;
        if (i == 12) scale = 22;
=======
    int a[5] = {0, 1, 10, 15, 22};
    for (int i = 1;i <= 4;i++){
        int scale = a[i];
        if (i == 11) scale = 15;
        if (i == 12) scale = 22;
        // if (i == 13) scale = 55;
>>>>>>> 22156990072ea76928f6d697531621f884a58bc5
        printf("====================Test %dk====================\n", scale);

        std::string f_size = std::to_string(scale)+"k";
        read_data_set(x+f_size, y+f_size);

        // init_MAT();
        init_opti_trie_struct();
        
        insert_rule();

        // print_info(scale);
        print_trie_info();

        query_packets(); 

        // delete_MAT();
        delete_opti_trie_struct();
    }
}