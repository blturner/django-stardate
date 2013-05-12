(function() {

    var root = this;

    // Set options of js markdown parser
    marked.setOptions({
        gfm: true,
        pedantic: false,
        sanitize: false,
        highlight: function(code, lang) {
            if (lang !== undefined) {
                var highlighted = root.hljs.highlight(lang, code).value;
                return highlighted;
            } else {
                return code;
            }
        }
    });

    // Solo Editor Application
    var Solo = function(options) {

        var self = this;

        if (options && options.markdown) this.markdown = options.markdown;
        if (options && options.preview) this.preview = options.preview;

        this.initialize = function() {
            self.editor = root.CodeMirror.fromTextArea(self.markdown, {
                    mode: 'gfm', // github flavored markdown
                    lineNumbers: true,
                    tabMode: "spaces",
                    matchBrackets: true,
                    theme: "monokai"
            });
            self.editor.on("change", self.timeUpdate);

            this.render(); // initial render on load
        };

        var timer;
        this.timeUpdate = function() {
            // Only render new preview after 500ms wait instead of every key
            clearTimeout(timer);
            timer = setTimeout(self.render, 200);
        };

        this.render = function() {
            self.editor.save(); // Save markdown to textarea

            var rendered = marked(self.markdown.value);
            self.preview.innerHTML = rendered;
        };


        this.initialize();

        return this;
    };

    root.Solo = Solo;

})();