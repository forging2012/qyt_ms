from django.shortcuts import render, HttpResponse, redirect
from choose import models
import json
from ldap3 import Server, Connection, NTLM, ALL

# Create your views here.


TOTAL_COUNT = 3
login_status = False


def login(request):
    if request.method == "POST":
        ret = {"status": False, "message": None}
        name = request.POST.get("name", None)
        pwd = request.POST.get("pwd", None)
        if not name or not pwd:
            ret["message"] = "用户名或密码不能为空！"
            return HttpResponse(json.dumps(ret))

        server = Server('ldap://172.16.66.6', use_ssl=True)
        try:
            conn = Connection(server, user="qytang\\%s" % name, password=pwd, authentication=NTLM, auto_bind=True)
            d = conn.extend.standard.who_am_i()
            print(d)
        except Exception as e:
            print("用户登录出现错误： ", e)
            ret["message"] = "用户名或密码错误！"
            return HttpResponse(json.dumps(ret))

        global login_status
        request.session['username'] = name
        ret["status"] = True
        login_status = True
        user = models.User.objects.filter(e_name=name)
        if not user:
            models.User.objects.create(e_name=name, c_name=name)
        return HttpResponse(json.dumps(ret))

    return render(request, "login.html")


def logout(request):
    global login_status
    try:
        del request.session["username"]
        login_status = False
    except:
        pass
    return redirect("/test/")


def test(request):
    if request.method == "GET":
        user_name = request.session.get('username', None)
        rock_name = request.GET.get("rock", "CCNAsec")
        rocks = models.Rocks.objects.all()
        test_beds = models.TestBeds.objects.filter(rock__rock_name=rock_name)
        rows = models.Rows.objects.filter(test_bed__rock__rock_name=rock_name)
        weekdays = models.Weekdays.objects.all()
        nodes = models.Nodes.objects.filter(row__test_bed__rock__rock_name=rock_name)
        return render(request, "index.html", {"test_beds": test_beds,
                                              "rows": rows,
                                              "weekdays": weekdays,
                                              "nodes": nodes,
                                              "rocks": rocks,
                                              "rock_name": rock_name,

                                              "user_name": user_name})

def node(request):
    if request.method == "POST":
        ret = {"status": False, "message": None, "name": None}
        if not login_status:
            ret["message"] = "尚未登陆，不能选择时间段！"
            return HttpResponse(json.dumps(ret))
        name = request.session["username"]
        rock = request.POST.get("rock", None)
        test_bed = request.POST.get("test_bed", None)
        weekday = request.POST.get("weekday", None)
        time_zone = request.POST.get("time_zone", None)
        node = models.Nodes.objects.get(weekday__day_name=weekday,
                                        row__time_zone=time_zone,
                                        row__test_bed__bed_name=test_bed,
                                        row__test_bed__rock__rock_name=rock)
        count = models.Nodes.objects.filter(row__test_bed__rock__rock_name=rock, owner__e_name=name).count()
        if not node.owner and count < TOTAL_COUNT:
            current_user = models.User.objects.get(e_name=name)
            node.owner = current_user
            node.save()
            ret["status"] = True
            ret["name"] = current_user.c_name
        else:
            ret["message"] = "每人每周每种Rack类型只能选择三个时间节点，你已选满！"
        return HttpResponse(json.dumps(ret))
    return redirect("/test")


def add_nodes(request):
    """
    用来初始化588个时间段节点，只允许运行一次！！！！
    :param request:
    :return:
    """
    row_list = models.Rows.objects.all()
    weekdays = models.Weekdays.objects.get(day_name="周日")
    for rows in row_list:
        models.Nodes.objects.create(weekday=weekdays, row=rows)
    return HttpResponse("ok")