const result_card_template = `
<div class='col-xl-6 col-lg-12'>
    <div class="card mb-3" style="padding: 20px 30px 10px 30px;">
        <div class="row align-items-center">
            <div class="col-md-4">
                <a href="https://www.dlsite.com/maniax/work/=/product_id/RJID.html"  target="_blank">
                    <img src="SMALL_IMG_LINK" class="card-img">
                </a>
            </div>
            <div class="col-md-8">
                <div class="card-body">
                    <h5 class="card-title">
                        <p class="genre-label btn btn-secondary">GENRE_BUTTON</p>
                        <b>TITLE</b>
                    </h5>
                    <p class="card-text">
                        META
                    </p>
                    <p>
                        <small class="card-text">
                            DESCRIPTION
                        </small>
                    </p>
                    <p>
                        LABEL_BUTTON
                    </p>
                    <div class="progress">
                        <div class="progress-bar" style="width: SIMILAR%;">SIMILAR%</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`;
const search_label_template = `
<div class="btn-group">
    <button class="btn btn-primary label label-search">TEXT</button>
    <button class="btn btn-primary label btn-del"><i class="fas fa-times"></i></button> 
</div>
`;
const include_label_template = `
<button class="btn btn-outline-primary label btn-del">TEXT <i class="fas fa-times"></i></button>
`;
const exclude_label_template = `
<button class="btn btn-outline-danger label btn-del">TEXT <i class="fas fa-times"></i></button>
`;
const genre_class_template = `
<div class="mb-3">
    <p>
        <button class="btn btn-expand" data-bs-toggle="collapse" data-bs-target="#genre-class-0IND">
            <b>TEXT</b>　
            <i class="fas fa-chevron-down"></i>
        </button>
    </p>
    <div id="genre-class-0IND" class="collapse"></div>
</div>
<hr>
`;
const genre_individual_template = `
<div class="btn-group">
    <button class="btn btn-outline-secondary label label-add" id="genre-IND" data-bs-toggle="tooltip" data-bs-html="true" title="有這個標籤的作品數：<b>NUM</b>">
        <b>TEXT </b>
        <i class="fas fa-plus"></i>
    </button> 
</div>
`;

const search_genres = new Set();
const include_genres = new Set();
const exclude_genres = new Set();
var current_rj_id = "";

$(document).ready(function () {
    var result_Collapse = new bootstrap.Collapse($("#result-container")[0], {
        toggle: false
    });
    var input_tip = new bootstrap.Collapse($("#input-tip-container")[0], {
        toggle: false
    });
    var work_tip = new bootstrap.Collapse($("#work-tip-container")[0], {
        toggle: false
    });

    // revise later
    window.onscroll = function () { scrollFunction() };
    function scrollFunction() {
        mybutton = $("#myBtn")[0];
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            mybutton.style.display = "block";
        } else {
            mybutton.style.display = "none";
        }
    }

    // 新增標籤子函數
    function add_search_genre(name) {
        if (!search_genres.has(name)) {
            search_genres.add(name);
            $("#genre-container").append(search_label_template.replace('TEXT', name));
            $("#genre-container .label-search").tooltip({
                title: "點選以強制包含此標籤",
                trigger: "hover",
            });
            clearwork();
            $("#modal-main-container").append(include_label_template.replace('TEXT', name));
        }
    }

    function add_include_genre(name) {
        if ((!include_genres.has(name) && $("#included-container .btn-del").length < 5)) {
            include_genres.add(name);
            $("#included-container").append(include_label_template.replace('TEXT', name));
            $("#included-tip").css("display", "none");
            $("#modal-main-container").append(include_label_template.replace('TEXT', name));
        }
    }

    function add_exclude_genre(name) {
        if ((!exclude_genres.has(name) && !search_genres.has(name) && !include_genres.has(name) && $("#excluded-container .btn-del").length < 5)) {
            exclude_genres.add(name);
            $("#excluded-container").append(exclude_label_template.replace('TEXT', name));
            $("#modal-main-container").append(include_label_template.replace('TEXT', name));
        }
    }

    // 清除作品欄位資訊
    function clearwork() {
        current_rj_id = "";
        $("#rjid").val("");
        $("#category-select").prop("disabled", false);
        $("#category-check").prop("disabled", true);
        $("#category-check").prop("checked", false);
        work_tip.hide();
    }

    // 表單互動用
    $("#popular-range").on("input", function () {
        var val = $(this).val();
        if (val < 20) {
            $("#popular-tip").html("非常熱門");
        } else if (val < 40) {
            $("#popular-tip").html("偏向熱門");
        } else if (val < 60) {
            $("#popular-tip").html("不加權");
        } else if (val < 80) {
            $("#popular-tip").html("偏向冷門");
        } else if (val < 100) {
            $("#popular-tip").html("非常冷門");
            $('#low-rate-check').prop('checked', true);
        } else if (val == 100) {
            $("#popular-tip").html("高山流水");
            $('#low-rate-check').prop('checked', false);
        }
    });

    $("#date-range").on("input", function () {
        var val = $(this).val();
        if (val == 0) {
            $("#date-tip").html("不篩選");
        } else if (val < 15) {
            $("#date-tip").html("十年");
        } else if (val < 30) {
            $("#date-tip").html("五年");
        } else if (val < 45) {
            $("#date-tip").html("四年");
        } else if (val < 60) {
            $("#date-tip").html("三年");
        } else if (val < 75) {
            $("#date-tip").html("兩年");
        } else if (val < 85) {
            $("#date-tip").html("一年");
        } else if (val < 95) {
            $("#date-tip").html("半年");
        } else if (val <= 100) {
            $("#date-tip").html("三個月");
        }
    });

    $("#category-check").change(function () {
        if ($(this).prop('checked')) {
            $("#category-select").prop('disabled', true);
        } else {
            $("#category-select").prop('disabled', false);
        }
    });

    // 取得標籤列表
    $.getJSON("/api/genres/jp", function (data) {
        var ind = 1;
        Object.entries(data).forEach(([k, v]) => {
            $("#genre-form").append(genre_class_template.replace('TEXT', k).replaceAll('IND', ind));
            v.forEach(element => {
                var label_name = Object.keys(element)[0];
                var label_id = Object.values(element)[0][0];
                var label_count = Object.values(element)[0][1];
                $("#genre-class-0" + ind).append(genre_individual_template.replace('TEXT', label_name).replace('IND', label_id).replace('NUM', label_count));
            });
            ind += 1;
        });
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })
    });

    // 在上面完成初始化 //

    // 決定標籤頁面用
    $('#genre-select-Modal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var form_type = button.data('genres');
        var labels = "";
        $('#genre-form').data('genres', form_type);
        switch (form_type) {
            case "Add":
                search_genres.forEach(element => {
                    labels += include_label_template.replace("TEXT", element);
                });
                $("#modal-desc").html("最多只有十個標籤會被搜尋。<br>已新增的<b> 搜尋 </b>標籤：");
                $("#modal-main-container").html(labels);
                break;
            case "Included":
                include_genres.forEach(element => {
                    labels += include_label_template.replace("TEXT", element);
                });
                $("#modal-desc").html("最多只能篩選五個標籤。<br>已新增的<b> 包含 </b>標籤：");
                $("#modal-main-container").html(labels);
                break;
            case "Excluded":
                exclude_genres.forEach(element => {
                    labels += include_label_template.replace("TEXT", element);
                });
                $("#modal-desc").html("最多只能篩選五個標籤。<br>已新增的<b> 排除 </b>標籤：");
                $("#modal-main-container").html(labels);
                break;
        }
    });

    // 自動填入作品標籤
    $("#rjid").keyup(function () {
        var rj_id = $(this).val();
        var re = /^RJ\d\d\d\d\d\d$/;
        if (re.test(rj_id)) {
            $.ajax({
                url: "/api/works",
                data: { rj_id: rj_id },
                success: function (data) {
                    $("#genre-container .btn-group").remove();
                    search_genres.clear();
                    $("#category-check").prop("disabled", false);

                    current_rj_id = rj_id;
                    data['labels'].forEach(element => {
                        $("#genre-container").append(search_label_template.replace('TEXT', element));
                        search_genres.add(element);
                    });

                    $("#genre-container .label-search").tooltip({
                        title: "點選以強制包含此標籤",
                        trigger: "hover",
                    });
                    input_tip.hide();
                    work_tip.show();
                    $("#work-tip").html("<span class='text-info' style=''>TEXT</span>".replace("TEXT", data['title']));
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    work_tip.show();
                    $("#work-tip").html("<span class='text-danger'><i class='fas fa-exclamation-triangle'></i> 找不到此作品。</span>");
                }
            });
        } else {
            current_rj_id = "";
            work_tip.hide();
            $("#category-select").prop("disabled", false);
            $("#category-check").prop("disabled", true);
            $("#category-check").prop("checked", false);
        }
    });

    // 從列表新增標籤
    $("#genre-form").on("click", ".label-add", function () {
        var name = $.trim($(this).text());
        var form_type = $("#genre-form").data('genres');

        switch (form_type) {
            case "Add":
                add_search_genre(name);
                break;
            case "Included":
                add_include_genre(name);
                break;
            case "Excluded":
                add_exclude_genre(name);
                break;
        }
    });

    // 從搜尋列新增包含標籤
    $("#genre-container").on("click", ".label-search", function () {
        var name = $.trim($(this).text());
        add_include_genre(name);
    });

    // 移除標籤用的按鍵
    $("#btn-delall").click(function () {
        search_genres.clear();
        $("#genre-container .btn-group").remove();
        clearwork();
    });

    $("#modal-main-container").on("click", ".btn-del", function () {
        var form_type = $('#genre-form').data('genres');
        var name = $.trim($(this).text());
        switch (form_type) {
            case "Add":
                search_genres.delete(name);
                $(this).remove();
                $("#genre-container .label-search:contains(" + name + ")").parent().remove();
                clearwork();
                break;
            case "Included":
                include_genres.delete(name);
                $(this).remove();
                $("#included-container .btn-del:contains(" + name + ")").remove();
                if ($("#included-container .btn-del").length === 0) {
                    $("#included-tip").css("display", "inline-block");
                }
                break;
            case "Excluded":
                exclude_genres.delete(name);
                $(this).remove();
                $("#excluded-container .btn-del:contains(" + name + ")").remove();
                break;
        }
    });

    $("#genre-container").on("click", ".btn-del", function () {
        search_genres.delete($.trim($(this).prev().text()));
        $(this).parent().remove();
        clearwork();
    });

    $("#included-container").on("click", ".btn-del", function () {
        include_genres.delete($.trim($(this).text()));
        $(this).remove();
        if ($("#included-container .btn-del").length === 0) {
            $("#included-tip").css("display", "inline-block");
        }
    });

    $("#excluded-container").on("click", ".btn-del", function () {
        exclude_genres.delete($.trim($(this).text()));
        $(this).remove();
    });

    // 檢查標籤數量
    $("body").on('DOMSubtreeModified', '#genre-container', function () {
        var labels_len = $(".label-search").length;
        if (labels_len == 0) {
            $("#genre-container-tip").css("display", "inline-block");
        } else {
            $("#genre-container-tip").css("display", "none");
        }
        if ($("#rjid").val() == '') {
            if (labels_len >= 10) {
                input_tip.show();
                $("#input-tip").html("<span class='text-warning'><i class='fas fa-exclamation-triangle'></i> 只有前 10 個標籤會被搜尋。</span>");
            } else if ((labels_len > 7) || (labels_len < 3)) {
                input_tip.show();
                $("#input-tip").html("<span class='text-info'><i class='fas fa-info-circle'></i> 使用 3-7 個標籤以獲得較佳的結果。</span>");
            } else {
                input_tip.hide();
                $("#input-tip").html("");
            }
        }
    });

    // 搜尋
    $(".btn-search").click(function () {
        if (search_genres.size > 0) {
            var genres = Array.from(search_genres).join('+');
            var include = Array.from(include_genres).join('+');
            var exclude = Array.from(exclude_genres).join('+');
            var rj_id = current_rj_id === "" ? 'RJ000000' : current_rj_id;

            if ($("#result-container").hasClass('show')) {
                result_Collapse.hide();
            }
            $("#footer-quote").css("display", "none")

            $.ajax({
                url: "/api/similarity",
                data: {
                    genres: genres,
                    rj_id: rj_id,
                    weight_func: parseInt($('input[name=weight-func]:checked').val()),
                    popular: $("#popular-range").val(),
                    date: $("#date-range").val(),
                    all_age: $("#all-age-check").prop('checked'),
                    including_r15: $("#r15-check").prop('checked'),
                    excluding_low_rate: $("#low-rate-check").prop('checked'),
                    excluding_interest: $("#interest-check").prop('checked'),
                    exclusive_category: $("#category-check").prop('checked'),
                    categories: $("#category-select").val(),
                    included_genres: include,
                    excluded_genres: exclude,
                },
                success: function (data) {
                    setTimeout(function () {
                        $('#result_list').html("");
                        data.forEach(element => {
                            var work_id = 'RJ' + element['index'].padStart(6, '0');
                            html = result_card_template.replace('SMALL_IMG_LINK', get_img_url(element['img_url'], element['index']));
                            html = html.replace('RJID', work_id);
                            html = html.replace('GENRE_BUTTON', element['category']);
                            html = html.replace('TITLE', element['title']);
                            html = html.replace('META', '<b>' + element['group'] + '</b>  @ ' + element['date'].slice(0,10) + '（販売数：<b>' + element['sells'] + '</b>）');
                            html = html.replace('DESCRIPTION', element['description']);
                            html = html.replaceAll('SIMILAR', (element['similarity'] * 100).toPrecision(3));
                            var label = '';
                            element['labels'].forEach(l => {
                                label += '<span class="badge genre-badge">' + l + '</span>'
                            });
                            html = html.replace('LABEL_BUTTON', label);

                            $('#result_list').append(html);
                        });
                        result_Collapse.show();
                        $("#footer-quote").css("display", "block")
                    }, 500);
                    setTimeout(function () {
                        window.scrollTo(0, $('#result-row').offset().top);
                    }, 1500);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.log(jqXHR);
                    console.log(textStatus);
                    console.log(errorThrown);
                }
            });
        } else {
            console.log('No input!')
        }
    });
});

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function get_img_url(is_url, rj_id) {
    if (is_url) {
        round_rj_id = Math.ceil(rj_id / 1000) * 1000;
        round_rj_id = round_rj_id.toString().padStart(6, '0');
        pad_rj_id = rj_id.padStart(6, '0');
        return 'https://img.dlsite.jp/resize/images2/work/doujin/RJ' + round_rj_id + '/RJ' + pad_rj_id + '_img_main_240x240.jpg';
    } else {
        return 'www.dlsite.com/images/web/home/no_img_main.gif';
    }
}