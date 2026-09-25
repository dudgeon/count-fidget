#include "input.h"
void input_push(InputQueue *q,uint8_t raw,uint32_t time) {
    uint8_t next=(uint8_t)((q->head+1U)&(INPUT_QUEUE_SIZE-1U));
    q->latest.raw=raw;q->latest.time=time;
    if(q->gap || next==q->tail) {
        q->gap=1;if(q->dropped!=65535U)++q->dropped;return;
    }
    q->samples[q->head].raw=raw;q->samples[q->head].time=time;
    q->head=next; /* Publish only after the entire sample has been stored. */
}
InputResult input_take(InputQueue *q,InputSample *sample) {
    if(q->gap) {
        sample->raw=q->latest.raw;sample->time=q->latest.time;
        q->tail=q->head;q->gap=0;return INPUT_GAP;
    }
    if(q->tail==q->head)return INPUT_EMPTY;
    sample->raw=q->samples[q->tail].raw;sample->time=q->samples[q->tail].time;
    q->tail=(uint8_t)((q->tail+1U)&(INPUT_QUEUE_SIZE-1U));return INPUT_SAMPLE;
}
void input_apply(InputState *s,Counter *c,InputResult result,const InputSample *sample) {
    if(result==INPUT_GAP) {
        s->fault=true;s->reset_requested=false;
        /* Lost history cannot prove a press. Freeze increments; a fresh,
         * fully debounced reset explicitly starts a new trustworthy count. */
        c->increment.stable=false;c->increment.candidate=false;c->increment.since=sample->time;
        c->reset.stable=false;c->reset.candidate=(sample->raw&INPUT_RESET)!=0;c->reset.since=sample->time;
        c->awake=true;c->last_activity=sample->time;return;
    }
    if(result==INPUT_SAMPLE) {
        bool reset_was=c->reset.stable,dirty_was=c->dirty,overflow_was=c->overflow;
        uint32_t count_was=c->count;
        /* Track the real held increment level even while uncertain; otherwise
         * clearing ERR could synthesize a new press from an already-held key. */
        counter_sample(c,(sample->raw&INPUT_INCREMENT)!=0,
                       (sample->raw&INPUT_RESET)!=0,sample->time);
        if(s->fault) {
            if(!reset_was && c->reset.stable)s->reset_requested=true;
            else {c->count=count_was;c->dirty=dirty_was;c->overflow=overflow_was;}
        }
    }
}

/* These helpers are called only in the foreground. Journal saving remains
 * between latch persistence and confidence restoration in main. */
void input_persist_fault(InputState *s,InputFaultRead read,InputFaultWrite write,void *context) {
    if(s->fault && read(context)!=INPUT_FAULT_MARKER)
        (void)write(context,INPUT_FAULT_MARKER);
}
void input_after_commit(InputState *s,const Counter *c,uint32_t committed,
                        InputFaultWrite write,void *context) {
    if(s->reset_requested && !c->dirty && committed==0 && write(context,INPUT_FAULT_CLEAR)) {
        s->fault=false;s->reset_requested=false;
    }
}
