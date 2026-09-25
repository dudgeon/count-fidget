#include "app.h"
#include <string.h>
void app_init(App *a,const NvHal *h,uint32_t now) {
    memset(a,0,sizeof(*a));journal_load(&a->journal,h);
    counter_init(&a->counter,a->journal.count,now);
    a->input.fault=a->journal.fault;
    if(a->journal.scan_error)app_storage_error(a);
}
void app_input(App *a,InputResult result,const InputSample *s) {
    input_apply(&a->input,&a->counter,result,s);
    if(a->storage_failed && a->input.reset_requested &&
       a->input.revision!=a->failed_revision)a->storage_failed=false;
}
bool app_fault(const App *a){return a->input.fault || a->storage_failed;}
bool app_settled(const App *a) {
    return !a->journal.busy && a->journal.valid &&
           a->journal.count==a->counter.count && a->journal.fault==a->input.fault &&
           !a->input.reset_requested;
}
bool app_can_idle(const App *a) {
    return !a->journal.busy && (app_settled(a) || a->storage_failed);
}
void app_storage_error(App *a) {
    if(a->storage_failed)return;
    a->storage_failed=true;a->input.fault=true;
    a->input.reset_requested=false;++a->input.revision;
    a->failed_revision=a->input.revision;
}
void app_service(App *a,const NvHal *h,uint32_t now,bool power_good) {
    Journal *j=&a->journal;
    if(j->busy)journal_service(j,h,now);
    if(j->failed) {
        j->failed=false;app_storage_error(a);
    }
    if(j->completed) {
        j->completed=false;
        if(a->input.reset_requested && j->ticket==a->input.revision &&
           j->count==0 && !j->fault) {
            a->input.fault=false;a->input.reset_requested=false;
        }
        if(j->count==a->counter.count)a->counter.dirty=false;
    }
    if(!j->busy && !a->storage_failed && power_good) {
        bool fault=a->input.fault && !a->input.reset_requested;
        if(!j->valid || j->count!=a->counter.count || j->fault!=fault || a->input.reset_requested)
            (void)journal_begin(j,a->counter.count,fault,a->input.revision);
    }
}
