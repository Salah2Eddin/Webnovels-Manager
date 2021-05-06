window.onload = function() {
    var novel_data_element = document.querySelector("#novel_data")
    var novel_name = novel_data_element.dataset.novelName

    function go_to_current_chapter() {
        var current_chapter = document.querySelector('[data-chapter-title=' + localStorage.getItem(novel_name) + ']')
        if (current_chapter != null) {
            current_chapter.scrollIntoView();
        }
    }
    var observer = new IntersectionObserver(
        function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    localStorage.setItem(novel_name, entry.target.dataset.chapterTitle);
                }
            });
        }, { rootMargin: '0px 0px 0px 0px' });
    document.querySelectorAll('div.chapter').forEach(chapter => { observer.observe(chapter) });
    go_to_current_chapter()
}