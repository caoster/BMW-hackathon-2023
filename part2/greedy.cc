#include <cstdio>
#include <set>
#include <cmath>

#define buf_size 1000
#define full 10.5
#define cap 10.5 * 0.9
#define lbound 10.5 * 0.3
#define rbound 10.5 * 0.8
#define hours 31*24
#define eps 1e-3

char line[buf_size];
double change[32*24];
double energy[32*24][123];

void eat()
{
    while(getchar() != ',');
}

int main() 
{
    freopen("../data/Examples.csv", "r", stdin);
    fgets(line, buf_size, stdin);
    double in, out;
    for(int i = 1; i <= 31 * 24; ++i ) {
        eat();
        eat();
        eat();
        eat();
        eat();
        if (scanf("%lf,%lf", &in, &out) != 2) break;
        change[i] = in - out;
        fgets(line, buf_size, stdin);
    }
    //for (int i = 1; i <= 31 * 24; ++i ) printf("%.2f\n", change[i]);
   
    // std::set<int > s{1, 4, 2, -4, 9, -10};
    // for (auto i:s){
    //     printf("%d\n", i);
    // }
    // s.erase(*s.rbegin());
    // for (auto i:s){
    //     printf("%d\n", i);
    // }
    puts("read done");
    
    double consume = 0.0;
    
    std::set<std::pair<double, int>> bat;
    
    for (int i = 1; i <= 120; ++ i) {
        bat.insert(std::make_pair(cap, i));
        energy[0][i] = cap;
    }
    for (int hr = 1; hr <= hours; ++hr) {
        for (int i = 1; i <= 120; ++ i) {
            energy[hr][i] = energy[hr - 1][i];
        }
        if (change[hr] > 0) {
            double left_in = change[hr];

            while(left_in > eps) {
                auto b = *bat.begin();
                bat.erase(b);
                double to_cap = cap - b.first, real_in;
                if (left_in <= to_cap) {
                    real_in = left_in;

                } else {
                    real_in = to_cap;
                }
                
                left_in -= real_in;
                double new_en = b.first + real_in;
                
                energy[hr][b.second] = new_en;
                bat.insert(std::make_pair(new_en, b.second));
            }
        } else {
            double left_out = - change[hr];
            while(left_out > eps) {
                auto b = *bat.rbegin();
                bat.erase(b);
                double to_bottom = b.first, real_out;
                if (left_out <= to_bottom) {
                    real_out = left_out;
                    
                } else {
                    real_out = to_bottom;
                }
                printf("%d out from %d = %.2f, left %.2f \n", hr, b.second, real_out, left_out);
                left_out -= to_bottom;
                double new_en = b.first - real_out;
                
                energy[hr][b.second] = new_en;
                bat.insert(std::make_pair(new_en, b.second));
            }
        }
    }
    
    for (int i = 1; i <= 120; ++i) {
        for (int hr = 1; hr <= hours; ++hr) {
            double en = energy[hr][i], pre_en = energy[hr - 1][i];
            double nxt_en = hr == hours ? en : energy[hr + 1][i];
            double decay = 1e-4;
            double dod = abs(en - pre_en) / full;
            if (dod <= 0.5) decay *= dod / 0.5;
            if (en < lbound || en > rbound) decay *= 1.05;
            if ((en - pre_en) * (nxt_en - en) < 0) decay += 1e-6;
            consume += decay;
        }
    }
    
    printf("consumption = %.8f\n", consume);
    freopen("out.txt", "w", stdout);
    for (int hr = 1; hr <= hours; hr ++) {
        for (int i = 1; i <= 120; ++i) {
            printf("%d at %d = %.4f\n", i, hr, energy[hr][i]);
        }
    }
    
    return 0;
}