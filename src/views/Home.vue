<template>
    <div class="start" v-if="!enabled">
        <div class="error" v-if="message">{{ message }}</div>
        <h1>INFORMATION FOR AKROW</h1>
        <p>After pasteing the stream id then press enter</p>
        <img src="../images/Paste_Id.png" alt="">
        <input type="text" placeholder="Stream Id Here" @submit.prevent @keyup="submitId" v-model="chat_id">
    </div>
    <div class="title" v-if="enabled">
        <h1>Auto Donate!</h1>
        <p>use <span class="code">/join [roblox_username] [asset_id]</span> in chat to join the queue! (example: /join KaizzoChan 9255717471)</p>
        <p>The asset id is the Shirt/Gamepass that is for sale, it MUST be {{ robux }} robux or under! <br> Example: https://www.roblox.com/catalog/<span class="code">9255717471</span>/10 (the highlighted part is the asset id)</p>
        <p>Time until next donation:</p>
        <p class="timer">{{ minutes }}{{ seconds }}</p>
        <div v-if="show_inputs" class="inputs"><input type="text" v-model="robux" placeholder="robux"> robux per <input type="text" v-model="per_seconds" placeholder="seconds"> seconds <input type="button" @click="submitRobux" value="Submit"></div>
    </div>
    <div class="names" v-if="enabled">
        <div  class="name" v-for="person in names" :class="{selected: person.selected}">{{ person.name }}</div>
        
    </div>
</template>

<script>
    export default {
        data() {
            return {
                chat_id: null,
                enabled: false,
                names: [],
                index: 0,
                speed: 26,
                decrease_timer: false,
                time_left: 300,
                minutes: 5,
                seconds: ":00",
                ready: true,
                message: null,
                show_inputs: true,
                robux: 10,
                per_seconds: 300
            }
        },
        methods: {
            async submitRobux() {
                const response = await fetch('/api/robux', {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({robux:this.robux})
                })
                const json = await response.json()
                if (json.message) {this.message = json.message}
                this.show_inputs = false
                this.time_left = this.per_seconds
            },
            async submitId(e) {
                if (e.key == "Enter") {
                    const response = await fetch('/api/stream', {
                        method: 'POST',
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({stream_id:this.chat_id})
                    })
                    const json = await response.json()
                    if (json.message) {this.message = json.message}
                    if (json.status == "success") {
                        this.enabled = true
                        this.decrease_timer = true
                        this.decreaseTimer()
                    }

                }
            },
            async selectItems() {
                    this.ready = false
                    this.names[this.index].selected = true
                    await this.delay(this.speed-25)
                    this.names[this.index].selected = false
                    this.index++
                    this.ready = true
                    
                    if (this.index >= this.names.length) {
                        this.index = 0
                    }
                },
            async resetInterval(interval, speed) {
                clearInterval(interval)
                this.speed = speed
                interval = setInterval(this.selectItems, this.speed)
                return interval
            },
            getSeconds() {
                let random = Math.random()
                let scaled = Math.floor(random * (3000-2000+1)) + 2000
                return scaled
            },
            async shuffle() {

                
                let interval = setInterval(this.selectItems, this.speed)
                await this.delay(this.getSeconds())
                interval = await this.resetInterval(interval, 100)
                await this.delay(this.getSeconds())
                interval = await this.resetInterval(interval, 300)
                await this.delay(this.getSeconds())
                interval = await this.resetInterval(interval, 500)
                await this.delay(this.getSeconds())
                interval = await this.resetInterval(interval, 750)
                await this.delay(this.getSeconds())
                interval = await this.resetInterval(interval, 1000)
                await this.delay(this.getSeconds())
                clearInterval(interval)
                await this.delay(1000)
                this.names[this.index].selected = true 

                await fetch('/api/winner', {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({name:this.names[this.index].name})
                })
                console.log(this.per_seconds)
                this.time_left = this.per_seconds + 11
                this.decrease_timer = true

            },
            delay(ms) {
                return new Promise(resolve => {
                    setTimeout(resolve,ms)
                })
            },
            decreaseTimer() {
                
                setInterval(async () => {

                    // Time Decrease
                    if (!this.enabled) { return}
                    if (!this.decrease_timer) {return}
                    this.time_left -= 1
                    this.minutes = Math.floor(this.time_left/60)
                    let seconds = this.time_left%60
                    if (`${seconds}`.length == 1) {
                        this.seconds = `:0${seconds}`
                    } else {
                        this.seconds = `:${seconds}`
                    }

                    //add to the names list
                    const response = await fetch('/api/names')
                    const json = await response.json()
                    this.names = json.names


                    // Shuffle the names
                    if (this.time_left == 0) {
                        this.decrease_timer = false
                        this.shuffle()
                    }
    
                },1000)
                }
        },
        mounted () {
            document.addEventListener('keydown', (e) => {
                if (e.key == "Control") {
                    this.show_inputs = !this.show_inputs
                }
            })
           
        },
    }
</script>

<style>

.error {
    background-color: rgb(255, 113, 113);

    padding: 0.25rem;
    margin: 1rem;

    border-radius: 8px;

    font-size: 24px;
    color: white;
    
}

.start {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

img {
    width: 800px;
}

.timer {
    background-color: rgb(90, 224, 90);

    width: 75px;
    padding: 0.5rem;
    margin: auto;
    margin-top: 8px;

    border-radius: 8px;

    font-size: 24px;
}

p {
    margin: 0px;
    margin-top: 0.5rem;
}

.code {
    background-color: rgb(43, 43, 43);

    padding: 0.25rem;

    font-family: monospace;
    color: white;
}

h1 {
    margin: 0px;
}

.title {
    width: fit-content;
    margin: auto;
    text-align: center;
}

.name {
    background-color: rgb(226, 226, 226);

    display: inline-block;
    padding: 0.5rem;

    border-radius: 8px;
}

.selected {
    background-color: greenyellow;
    transition: all 0.125s;
}

.names {
    padding: 1rem;

    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    flex-wrap: wrap;
}

</style>