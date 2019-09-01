
new Vue({
    // 根DOM元素的CSS选择器
    el: '#notebook',
    // 一些数据
    data () {
        return {
            content: 'This is a note.'
        }
    },
    // 计算属性
    computed: {
        notePreview () {
            // Markdown渲染为HTML
            return marked(this.content)
        },
    },
})

//const html = marked('**Blod** *Italic* [link](http://vuejs.org/)')
//console.log(html)