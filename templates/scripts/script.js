$(document).ready(function() {
    var novel_data_element = $("#novel_data")[0]
    var novel_name = novel_data_element.dataset.novelName

    function go_to_current_chapter() {
        var current_chapter = $('[data-chapter-title="' + localStorage.getItem(novel_name) + '"]')
        if (current_chapter != null) {
            current_chapter[0].scrollIntoView();
        }
    }

    function swap_theme() {
        classes = document.children[0].classList;
        if (!classes.contains("dark-mode")) {
            classes.add('dark-mode');
            localStorage.setItem("dark-mode", true);
            return
        }
        classes.remove('dark-mode');
        localStorage.setItem("dark-mode", false);
        return
    }
    var observer = new IntersectionObserver(
        function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    localStorage.setItem(novel_name, entry.target.dataset.chapterTitle);
                }
            });
        }, { rootMargin: '0px 0px 0px 0px' });
    if (localStorage.getItem('dark-mode') == 'true') {
        swap_theme();
        document.querySelector("#theme-checkbox").checked = true;
    }
    document.querySelectorAll('div.chapter').forEach(chapter => { observer.observe(chapter) });
    document.querySelector("#theme-switcher").addEventListener('click', swap_theme);
    document.querySelector('#theme-switch-parent').classList.remove('hidden');
    go_to_current_chapter();

});