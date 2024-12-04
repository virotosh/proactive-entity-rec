$(document).ready(function () {
  // button color
  $( "#startStopTheLab" ).css('background-color', 'green');
  var socket = io();

  var selectedEntities = [];
  var people, applications, documents, topics;
  var dataKeys;
  var htmlListName = ["topicList", "applicationList", "documentList",  "peopleList"];
  var newData, oldData;
  var enterData, updateData, exitData;
  var appImageNames = [{"appType":"Skype", "imagePath":"./images/Skype.png"},
                        {"appType":"Microsoft.Word", "imagePath":"./images/MSWord.png"},
                        {"appType":"Microsoft.PowerPoint", "imagePath":"./images/MSPowerPoint.png"},
                        {"appType":"Microsoft.Excel", "imagePath":"./images/MSExcel.png"},
                        {"appType":"Sublime.Text", "imagePath":"./images/sublime_text.png"},
                        {"appType":"Mendeley.Desktop", "imagePath":"./images/mendeley_desktop.png"},
                        {"appType":"Safari", "imagePath":"./images/Safari.png"},
                        {"appType":"Terminal", "imagePath":"./images/Terminal.png"},
                        {"appType":"Xcode", "imagePath":"./images/Xcode.png"},
                        {"appType":"Finder", "imagePath":"./images/Finder.png"},
                        {"appType":"Preview", "imagePath":"./images/Preview.png"},
                        {"appType":"Mail", "imagePath":"./images/Mail.png"},
                        {"appType":"Filezilla", "imagePath":"./images/Filezilla.png"},
                        {"appType":"FaceTime", "imagePath":"./images/FaceTime.png"},
                        {"appType":"Evernote", "imagePath":"./images/Evernote.png"},
                        {"appType":"Slack", "imagePath":"./images/Slack.png"},
                        {"appType":"System.Preferences", "imagePath":"./images/System_Preferences.png"},
                        {"appType":"WeChat", "imagePath":"./images/WeChat.png"},
                        {"appType":"Calendar", "imagePath":"./images/Calendar.png"},
                        {"appType":"textedit", "imagePath":"./images/textedit.png"}];

  // socket.on('sendAllLists', function(data){
  // function renderInitialData (data) {
                  
  //socket.on('clickBehavior', function(data){
    //window.location = JSON.parse(data).user_openlink[0][1]
    //console.log(JSON.parse(data).user_openlink[0][1]);
  //});
  socket.on('entityData', function(data){
    oldData = newData;
    newData = JSON.parse(data);
    enterData = [], updateData = [], exitData = [];
    console.log('get all lists data from backend', newData);

    people = newData.people;
    applications = newData.applications;
    for (var app in applications)
    documents = newData.document_ID;
    topics = newData.keywords;
    dataKeys = Object.keys(newData);
    dataKeys.splice(dataKeys.indexOf("pair_similarity"), 1);
    // Salvatore
    var docMerged = new Map();
    for (var i = 0; i < documents.length; i++) {
    documents[i].push(i);
    //console.log(documents[i]);
    if (docMerged.has(documents[i][1])){
    var docTmp = docMerged.get(documents[i][1]);
    docTmp[6] = docTmp[6] + 1;
    docTmp.push(documents[i][3]);
    //console.log("docTmp: " + docTmp);
    //console.log(documents[i][3]);
    /*if (Math.abs(docTmp[0]-documents[i][1])<10) {
     console.log(Math.abs(docTmp[0]-documents[i][1]))
     docMerged.set(documents[i][1], docTmp);
     } */
    /*else {
     documents[i].push(0);
     docMerged.set(documents[i][1], documents[i]);
     }*/
    }
    else {
    documents[i].push(0);
    docMerged.set(documents[i][1], documents[i]);
    }
    }
    //console.log(docMerged)
    var iteratorDocMerged = docMerged.values();
    ////////////////////
    // create enterData and updateData
    for (var i = 0; i < dataKeys.length; i++) {
      for (var j = 0; j < newData[dataKeys[i]].length; j++) {
        var currentId = newData[dataKeys[i]][j][0];
        //var appType = newData[dataKeys[i]][j][4];
        //var imagePath = findImagePath(appType);
        var entityIcon, entityOpenType;

        // set the applications label
        if (dataKeys[i] == "applications") {
          newData[dataKeys[i]][j][1] = newData[dataKeys[i]][j][1].replace("_appname","").replace(/_/g , ".");
        }

        // set entityIcon
        if (dataKeys[i] == "applications") {
          var app_name = newData[dataKeys[i]][j][1];
          if (findImagePath(app_name) == "./images/default.png"){
            entityIcon = "https://www.google.com/s2/favicons?domain=" + url_domain(app_name);
          }
          else{
            entityIcon = findImagePath(app_name);
          }
        } else if (dataKeys[i] == "document_ID") {
          //entityIcon = newData[dataKeys[i]][j][3];
            //salvatore
            if (newData[dataKeys[i]].length > docMerged.size) newData[dataKeys[i]].splice(docMerged.size,newData[dataKeys[i]].length-docMerged.size);
            if (j<docMerged.size) {
            newData[dataKeys[i]][j] = iteratorDocMerged.next().value;
            currentId = newData[dataKeys[i]][j][0];
            entityIcon = newData[dataKeys[i]][j][3];
            if (newData[dataKeys[i]][j][6] > 1) newData[dataKeys[i]][j][1] = newData[dataKeys[i]][j][1] + " (" + newData[dataKeys[i]][j][6] + ")";
            }
            else {
            newData[dataKeys[i]][j] = undefined;
            entityIcon = undefined;
            continue;
            }
        } else {
          entityIcon = undefined;
        }

        // set entityOpenType
        if (dataKeys[i] == "document_ID") {
          // if there is no link to open, get the app type
          //if (newData[dataKeys[i]][j][2] == "" || newData[dataKeys[i]][j][2].includes("file://")) {
          if (newData[dataKeys[i]][j][2] == "" || newData[dataKeys[i]][j][2].includes("file://") || newData[dataKeys[i]][j][2].includes("message://")) {
            entityOpenType = findImagePath(newData[dataKeys[i]][j][4].replace(" " , "."));
          } else {
            entityOpenType = "https://www.google.com/s2/favicons?domain=" + url_domain(newData[dataKeys[i]][j][2]);
          }
        } else {
          entityOpenType = undefined;
        }

        var currentVisualEntity = { htmlListName:htmlListName[i], column:j, id:currentId.toString(), label:newData[dataKeys[i]][j][1], url:isNaN(newData[dataKeys[i]][j][2]) ? newData[dataKeys[i]][j][2] : "", entityIcon: entityIcon, entityOpenType: entityOpenType};
        if (!idInOldData(currentId)) {
          enterData.push(currentVisualEntity);
        } else {
          updateData.push(currentVisualEntity);
        }
      }
    }

    function url_domain(data) {
      var a = document.createElement('a');
      if (!data.startsWith("http://") && !data.startsWith("https://")) {
        data = "http://" + data;
      }
      a.href = data;
      return a.hostname;
    }

    function findImagePath(appType) {
        //console.log(appType)
      for (var i = 0; i < appImageNames.length; i++) {
        if (appImageNames[i].appType.toLowerCase() == appType.toLowerCase()) {
          return appImageNames[i].imagePath;
        }
      }
      return "./images/default.png";
    }

    // create exitData
    for (var i = 0; i < dataKeys.length; i++) {
      if (typeof oldData == 'undefined') {
        break;
      }
      for (var j = 0; j < oldData[dataKeys[i]].length; j++) {
        var currentId = oldData[dataKeys[i]][j][0];
        var currentVisualEntity = { htmlListName:htmlListName[i], column:j, id:currentId.toString(), label:oldData[dataKeys[i]][j][1]};
        if (!idInNewData(currentId)) {
          exitData.push(currentVisualEntity);
        }
      }
    }

    function idInOldData(id) {
      var oldDataId;
      if (typeof oldData == 'undefined') {
        return false;
      }
      for (var i = 0; i < dataKeys.length; i++) {
        for (var j = 0; j < oldData[dataKeys[i]].length; j++) {
          oldDataId = oldData[dataKeys[i]][j][0];
          if (oldDataId == id) {
            return true;
          }
        }
      }
      return false;
    }

    function idInNewData(id) {
      var newDataId;
      for (var i = 0; i < dataKeys.length; i++) {
        for (var j = 0; j < newData[dataKeys[i]].length; j++) {
          newDataId = newData[dataKeys[i]][j][0];
          if (newDataId == id) {
            return true;
          }
        }
      }
      return false;
    }

    // for enterData, add the div
    for (var i = 0; i < enterData.length; i++) {
      $( "#"+enterData[i].htmlListName )
        .append($('<div></div>')
          .addClass("entity")
          // .css({"left":enterData[i].column * 270 + "px"})
          .css({"left": "1280px"})
          .animate({"left":enterData[i].column * 250 + "px"}, 1000)
          .click(function(ev) {
            var label, id, entityIcon, entityOpenType;
            var htmlListName = $(ev.target).parents(".list").attr("id");
            var selectStatusWhenClicking = null;

            // toggle class/bg
            //  if we click "open", we do nothing
            if ($(ev.target).hasClass("open")) {
              return;
            }
            //  else, we interact with backend
            if ($(ev.target).hasClass("entity")) {
              label = $(ev.target).find(".label").text();
              id = $(ev.target).find(".profile").attr("class").match(/id[\w-]*\b/)[0].substr(2);
              entityIcon = $(ev.target).find("img.entityIcon").attr("src");
              entityOpenType = $(ev.target).find("img.entityOpenType").attr("src");

              $(ev.target).toggleClass("selected");
              if ($(ev.target).hasClass("selected")) {
                selectStatusWhenClicking = false;
              } else {
                selectStatusWhenClicking = true;
              }
            } else {
              label = $(ev.target).parents(".entity").find(".label").text();
              id = $(ev.target).parents(".entity").find(".profile").attr("class").match(/id[\w-]*\b/)[0].substr(2);
              entityIcon = $(ev.target).parents(".entity").find("img.entityIcon").attr("src");
              entityOpenType = $(ev.target).parents(".entity").find("img.entityOpenType").attr("src");

              $(ev.target).parents(".entity").toggleClass("selected");
              if ($(ev.target).parents(".entity").hasClass("selected")) {
                selectStatusWhenClicking = false;
              } else {
                selectStatusWhenClicking = true;
              }
            }
            // toggle selection
            toggleSelection({ htmlListName:htmlListName, id:id.toString(), label:label, entityIcon:entityIcon, entityOpenType:entityOpenType});

            if (selectStatusWhenClicking) {
              socket.emit('userFeedback', JSON.stringify({"user_feedback":[[id, 0]]}));
              console.log(JSON.stringify({"user_feedback":[[id, 0]]}));
            } else {
              socket.emit('userFeedback', JSON.stringify({"user_feedback":[[id, 1]]}));
              // if (id == "7") {
              //   socket.emit('send1AfterSkpyeData');
              // } else if (id == "388") {
              //   socket.emit('send2AfterFBData');
              // } else if (id == "3049") {
              //   socket.emit('send3AfterTuukkaData');
              // } else if (id == "2699") {
              //   socket.emit('send2AfterFBData');
              // }
              console.log(JSON.stringify({"user_feedback":[[id, 1]]}));
            }
          })
          .append($('<div></div>')
            .addClass("profile id" + enterData[i].id)
            .prepend($('<img src='+ (typeof enterData[i].entityIcon != 'undefined' ? enterData[i].entityIcon : '') + ' />')
              .addClass("entityIcon"))
            .prepend($('<img src='+ (typeof enterData[i].entityOpenType != 'undefined' ? enterData[i].entityOpenType : '') + ' />')
              .addClass("entityOpenType")))
          .append($('<div></div>')
            .addClass("label"))
          .append($('<a></a>')
            //.addClass("open " + (enterData[i].url.length == 0 ? " hide" : ""))
            //.attr('href', enterData[i].url)
            .addClass("open ")
            .attr('href', (enterData[i].url.length == 0 ? enterData[i].entityIcon : enterData[i].url.split(',')[0]))
            .attr('id', enterData[i].id)
            .on('click', function() {
                socket.emit('userFeedback', JSON.stringify({"user_openlink":[[$(this).attr('id'), $(this).attr('href')]]}));
                console.log( "userOpenLink: " + $(this).attr('id') );
                })
            .attr('target', '_blank')
            .text("open")));

      var displayedLabel = enterData[i].label;
      var subDisplayedLabel;
      var lastIndexOfSpace;
      var oneLineCharNum = 25;

      // for applications, replace "_" with "."
      // if (enterData[i].htmlListName == "applicationList") {
      //   displayedLabel = displayedLabel.replace(/_/g , ".");
      // }

      // for document title, put to 2 lines and trim it if too long
      if (enterData[i].htmlListName == "documentList") {
        subDisplayedLabel = displayedLabel.substr(0, oneLineCharNum - 1);
        lastIndexOfSpace = subDisplayedLabel.lastIndexOf(" ");
        // for the first line
        //  if the first line does not have space, we break it after 32th char
        if (lastIndexOfSpace == -1) {
          displayedLabel = displayedLabel.slice(0, oneLineCharNum) + "\n" + displayedLabel.slice(oneLineCharNum);
          // for the second line
          if (displayedLabel.length > oneLineCharNum * 2 + 1) {
            displayedLabel = displayedLabel.slice(0, oneLineCharNum * 2) + "…";
          }
        }
        //  if the first line has space, we break it after the last space
        else {
          displayedLabel = displayedLabel.slice(0, lastIndexOfSpace) + "\n" + displayedLabel.slice(lastIndexOfSpace + 1);
          // for the second line
          if (displayedLabel.length - lastIndexOfSpace - 1 > oneLineCharNum) {
            displayedLabel = displayedLabel.slice(0, lastIndexOfSpace + 1 + (oneLineCharNum - 1)) + "…";
          }
        }
      }

      $('#' + enterData[i].htmlListName + ' .id' + enterData[i].id).parents(".entity").find(".label").text(displayedLabel);
    }

    // for updateData, change the position
    for (var i = 0; i < updateData.length; i++) {
      $(' .id' + updateData[i].id).parents(".entity").animate({"left":updateData[i].column * 250 + "px"}, 1000);
    }

    // for exitData, change the position
    for (var i = 0; i < exitData.length; i++) {
      if (exitData.length == 0) {
        break;
      }
      var $entity = $('#flowingArea .id' + exitData[i].id).parents(".entity");
      $entity.fadeOut(1000);
      setTimeout(function(){
        $entity.remove();
      }, 1000)
    }
  });
  // }
  function clickOpen(id){
    console.log("On link clicked");
    console.log(id);
  }
                  
  function toggleSelection(entity) {
    if (selectedEntities.map(function(a) {return a.id;}).indexOf(entity.id) == -1) {
      selectedEntities.push(entity);
    } else {
      selectedEntities.splice(selectedEntities.map(function(a) {return a.id;}).indexOf(entity.id), 1);
    }
    updateSecreenSeletedList();
  }
  

  function updateSecreenSeletedList() {
    if (selectedEntities.length == 0) {
      $("#selection").text("Select items to interact with");
      $("#selection").addClass("empty");
    } else {
      $("#selection").text("");
      $("#selection").removeClass("empty");
      $("#selection").find(".entity").remove();

      var lineCharNum = 17;

      for (var i = 0; i < selectedEntities.length; i++) {
        $("#selection")
          .append($('<div></div>')
            .addClass("entity " + selectedEntities[i].htmlListName)
            .append($('<div></div>')
              .addClass("profile id" + selectedEntities[i].id)
              .prepend($('<img src='+ (typeof selectedEntities[i].entityIcon != 'undefined' ? selectedEntities[i].entityIcon : '') + ' />')
                .addClass("entityIcon"))
              .prepend($('<img src='+ (typeof selectedEntities[i].entityOpenType != 'undefined' ? selectedEntities[i].entityOpenType : '') + ' />')
                .addClass("entityOpenType")))
            .append($('<div></div>')
              .addClass("label")
              .text(selectedEntities[i].label.length > lineCharNum ? selectedEntities[i].label.slice(0, lineCharNum - 1) + "…" : selectedEntities[i].label))
            .append($('<div>x</div>')
              .addClass("delete")
              .click(function(ev) {
                var id;
                if ($(ev.target).hasClass("entity")) {
                  id = $(ev.target).find(".profile").parents(".entity").attr("class").match(/id[\w-]*\b/)[0].substr(2);
                } else {
                  id = $(ev.target).parents(".entity").find(".profile").attr("class").match(/id[\w-]*\b/)[0].substr(2);
                }

                //update front-end
                selectedEntities.splice(selectedEntities.map(function(a) {return a.id;}).indexOf(id), 1);
                $("#flowingArea").find(".id" + id).parents(".entity").toggleClass("selected");
                updateSecreenSeletedList();

                //update back-end
                socket.emit('userFeedback', JSON.stringify({"user_feedback":[[id, 0]]}));
                console.log(JSON.stringify({"user_feedback":[[id, 0]]}));
              })));
      }
    }
  }

  $( "#clearSelection" ).click(function(){
    $('.entity').removeClass("selected");
    var id;
    for (var i = (selectedEntities.length - 1); i >= 0; i--) {
      id = selectedEntities[i].id;
      socket.emit('userFeedback', JSON.stringify({"user_feedback":[[id, 0]]}));
      console.log(JSON.stringify({"user_feedback":[[id, 0]]}));
      selectedEntities.splice( i, 1);
    }
    updateSecreenSeletedList();
  });

  $( "#sendInitialDataButton" ).click(function(){
    // socket.emit('sendInitialData');
    var data =  '{"keywords": [[1024, "helsinki", 0.027330681526756453], [964, "inbox", 0.025122878365005451], [1089, "backend", 0.0188934687012789], [974, "meeting", 0.010450761491786101], [906, "sent", 0.010257566246292803], [996, "mailboxes", 0.0089467242094154048], [892, "frontend", 0.0081074371391200231], [34344, "corpus", 0.0073102699071895061], [1105, "model", 0.0073014249850533895], [924, "flagged", 0.0070300270791934568]], "applications": [[905, "mail", 0.0095259746352726812], [4738, "skype", 0.004877624898629104], [4452, "moodle_helsinki_fi", 0.00085389497745726856], [80352, "webmail_cs_helsinki_fi", 0.00052485601585871493], [1179, "outlook_office_com", 0.0005124759683971296], [4992, "slides_com", 0.00047158472928288217], [4278, "preview", 0.00023297949509395674], [81349, "docs_google_com", 0.00021828268939477372], [5325, "www_slideshare_net", 0.00017474404870873163], [10524, "www_youtube_com", 0.00016529221912618924]], "pair_similarity": [[1024, 4992, 0.078297460662333423], [1024, 4738, -0.040599488752266752], [1024, 1031, -0.020770242706227109], [1024, 905, 0.23868142889433286], [1024, 906, 0.39440949261029923], [1024, 1037, -0.0019448085648117776], [1024, 911, 0.031888186837872277], [1024, 921, 0.0068333456689899192], [1024, 2202, -0.006586830386395421], [1024, 1179, 0.025760330549654997], [1024, 924, 0.53168266659900831], [1024, 34344, -0.021693620160485157], [1024, 10524, -0.011335129639093274], [1024, 942, 0.80900238423504134], [1024, 37298, 0.81426924145000346], [1024, 4278, -0.0039257206943426022], [1024, 1089, 0.067803557702872275], [1024, 964, 0.78459179161946446], [1024, 81349, -0.0068278110404116172], [1024, 5325, -0.019496749717335771], [1024, 974, 0.01182815500345619], [1024, 1105, -0.013201681783606182], [1024, 978, -0.014078889271402941], [1024, 980, 0.014729623319688611], [1024, 996, 0.49463437220056899], [1024, 80352, 0.40526963849184977], [1024, 4452, 0.26431130448189855], [1024, 1010, 0.52567651641914892], [1024, 892, 0.0054930527431397329], [4992, 4738, -0.015102900868934324], [4992, 1031, -0.019575155761721055], [4992, 905, 0.41624196851164019], [4992, 906, 0.014598399595491168], [4992, 1037, -0.086763844229057155], [4992, 911, 0.085480597412330842], [4992, 921, -0.0079752115542895737], [4992, 2202, -0.03634239045179475], [4992, 1179, 0.26246957765672513], [4992, 924, 0.012829631504148479], [4992, 34344, -0.0070277321368287099], [4992, 10524, -0.010406535047693543], [4992, 942, 0.069646362094986494], [4992, 37298, 0.12134391021144757], [4992, 4278, -0.014872546638016515], [4992, 1089, 0.13841835327272745], [4992, 964, 0.044055883271332349], [4992, 81349, 0.018335250009273132], [4992, 5325, -0.041992704779167715], [4992, 974, -0.022819738019427594], [4992, 1105, -0.059731499226957932], [4992, 978, -0.064700286347528266], [4992, 980, 0.09564491356490773], [4992, 996, 0.0013339884243356384], [4992, 80352, 0.0065705797884019557], [4992, 4452, 0.00027979320368860295], [4992, 1010, 0.054288634904469141], [4992, 892, -0.049532324372691637], [4738, 1031, 0.20410400611142393], [4738, 905, -0.080517041506609183], [4738, 906, 0.34393562616746054], [4738, 1037, -0.01894875279161044], [4738, 911, 0.07589669432067099], [4738, 921, 0.072012716085119513], [4738, 2202, -0.065278620368141707], [4738, 1179, 0.0035272780284851118], [4738, 924, -0.052947083963053969], [4738, 34344, -0.0033405490126565554], [4738, 10524, -0.016661278854338411], [4738, 942, -0.023524058299634637], [4738, 37298, -0.025837019976870528], [4738, 4278, 0.00084724809562483226], [4738, 1089, 0.17278664851499892], [4738, 964, -0.051178961261751324], [4738, 81349, -0.043574718055353699], [4738, 5325, -0.014325506359685608], [4738, 974, 0.0030662368661616762], [4738, 1105, -0.014842929404179483], [4738, 978, -0.0019259986285509797], [4738, 980, 0.16432611353990728], [4738, 996, -0.053973490308730554], [4738, 80352, -0.014043301057621875], [4738, 4452, -0.026283470675537008], [4738, 1010, -0.049807578298613986], [4738, 892, -0.013086766341977392], [1031, 905, 0.050791063159114754], [1031, 906, 0.22387912233510371], [1031, 1037, 0.043205785282998919], [1031, 911, 0.31880058072484446], [1031, 921, 0.45869928774245927], [1031, 2202, 0.11050914356651195], [1031, 1179, 0.0094990392345471499], [1031, 924, 0.12013817735898293], [1031, 34344, 0.006439303220152643], [1031, 10524, 0.016359444931252493], [1031, 942, 0.037524201256577322], [1031, 37298, -0.056921742900984215], [1031, 4278, -0.0099139977377383122], [1031, 1089, 0.43488667335023889], [1031, 964, 0.031831355255033653], [1031, 81349, -0.005399983751419246], [1031, 5325, -0.025661543864056016], [1031, 974, 0.0030123439585028082], [1031, 1105, 0.15369382427036582], [1031, 978, 0.062751298208330933], [1031, 980, 0.054416292708278052], [1031, 996, 0.12181686690466301], [1031, 80352, -0.079702407913050097], [1031, 4452, -0.042253712119615823], [1031, 1010, 0.1231953691364628], [1031, 892, 0.27943660097215922], [905, 906, 0.3603418667323412], [905, 1037, 0.018857117401199684], [905, 911, 0.10008657409197473], [905, 921, 0.10565111223189093], [905, 2202, 0.083488184373609095], [905, 1179, 0.21489907276851339], [905, 924, 0.36754514896430568], [905, 34344, 0.0078948646516943076], [905, 10524, -0.013531796650861325], [905, 942, 0.16030538434802671], [905, 37298, 0.18414104411752655], [905, 4278, 0.023888668703308549], [905, 1089, 0.16507438235018096], [905, 964, 0.25588364816592263], [905, 81349, -0.052828214198848769], [905, 5325, 0.0066010534440549724], [905, 974, -0.015014530275951449], [905, 1105, -0.081905212440707933], [905, 978, 0.10135365835779753], [905, 980, 0.11757875304701694], [905, 996, 0.36826115535231752], [905, 80352, -0.01258481926138481], [905, 4452, 0.12860825733750994], [905, 1010, 0.39265508368239543], [905, 892, -0.0013953035887854205], [906, 1037, -0.03175279239340173], [906, 911, 0.13329027016099124], [906, 921, 0.11677006894363301], [906, 2202, 0.11906049778898367], [906, 1179, 0.4116025995301747], [906, 924, 0.67197335913296952], [906, 34344, 0.017506174171493468], [906, 10524, 0.0075183720820591491], [906, 942, 0.44046542932481553], [906, 37298, 0.40786728829931523], [906, 4278, 0.0023248174444561905], [906, 1089, 0.1351883004020796], [906, 964, 0.64754955538517411], [906, 81349, -0.053929986739142594], [906, 5325, -0.0032290156264395621], [906, 974, -0.0017254976026514748], [906, 1105, -0.016585566463537281], [906, 978, 0.056765255262145334], [906, 980, 0.21854487179720938], [906, 996, 0.67371644525242058], [906, 80352, -0.018921920444230956], [906, 4452, -0.21618263200576546], [906, 1010, 0.67468709475666355], [906, 892, 0.0097556852347867873], [1037, 911, 0.11280730322089308], [1037, 921, 0.82541151680101521], [1037, 2202, 0.041388400752442621], [1037, 1179, -0.021120718970576539], [1037, 924, -0.026192148423854852], [1037, 34344, -0.023732478860146011], [1037, 10524, 0.0043037873963739093], [1037, 942, -0.061044627315984597], [1037, 37298, -0.053288612223539956], [1037, 4278, 0.0059957293698141801], [1037, 1089, 0.13853920318667065], [1037, 964, -0.077732787099660375], [1037, 81349, -0.019407021937905958], [1037, 5325, -0.0026606588936670581], [1037, 974, 0.027421355824082082], [1037, 1105, 0.56301538972011933], [1037, 978, 0.96852741558411537], [1037, 980, 0.095081993071715026], [1037, 996, -0.023776719807296801], [1037, 80352, 0.031965573860735057], [1037, 4452, -0.070632812942804601], [1037, 1010, -0.027568783969478917], [1037, 892, 0.25177217241120892], [911, 921, 0.39429725282412059], [911, 2202, 0.16695889721883395], [911, 1179, -0.032031041438060272], [911, 924, 0.015932518256238346], [911, 34344, 0.042515599296447645], [911, 10524, 0.037295882327172791], [911, 942, 0.012297725861941963], [911, 37298, -0.012393469424764936], [911, 4278, 0.002424223379588383], [911, 1089, 0.6314158221993813], [911, 964, 0.0080960726041805434], [911, 81349, 0.046286624797916877], [911, 5325, -0.012766612096948862], [911, 974, -0.0059745537208348767], [911, 1105, -0.055536930491916256], [911, 978, 0.13428796796045037], [911, 980, 0.60658003896630297], [911, 996, 0.012671316501410892], [911, 80352, 0.043330882410182819], [911, 4452, 0.075599894319591451], [911, 1010, 0.0093644486144501826], [911, 892, 0.14789850631989257], [921, 2202, 0.04986989849107637], [921, 1179, -0.010593737227013084], [921, 924, 0.051614070394157024], [921, 34344, 0.050672550277233913], [921, 10524, 0.006811568285312139], [921, 942, -0.010493856178373095], [921, 37298, -0.04811536693870886], [921, 4278, 0.013750226750763475], [921, 1089, 0.48848276634842652], [921, 964, -0.037248684493645642], [921, 81349, -0.0030648855676929676], [921, 5325, -0.01396139637615643], [921, 974, 0.015171442532497977], [921, 1105, 0.4096633259932001], [921, 978, 0.83501159336479291], [921, 980, 0.30491889266378036], [921, 996, 0.052653254062173895], [921, 80352, 0.023700279562228668], [921, 4452, -0.055747524659454754], [921, 1010, 0.049209828255201843], [921, 892, 0.39316037019378608], [2202, 1179, -0.078540778465423303], [2202, 924, 0.20850473543800305], [2202, 34344, -0.0011970703389799786], [2202, 10524, 0.06000847877910058], [2202, 942, 0.056398566017176285], [2202, 37298, -0.01433783531698939], [2202, 4278, 0.0084123209191915502], [2202, 1089, 0.23462514504810456], [2202, 964, 0.072304643270536151], [2202, 81349, 0.0074183501281079711], [2202, 5325, -0.029029044330169517], [2202, 974, 0.0010432590496356243], [2202, 1105, 0.14553689806309372], [2202, 978, 0.037902360849646613], [2202, 980, 0.21883652198912457], [2202, 996, 0.21074206561404277], [2202, 80352, -0.2091773505065419], [2202, 4452, -0.030762621351430684], [2202, 1010, 0.18953877597420352], [2202, 892, -0.10628166540205523], [1179, 924, -0.12311142736855984], [1179, 34344, -0.0038527166334202381], [1179, 10524, -0.032998218532993832], [1179, 942, -0.11348010513049389], [1179, 37298, -0.091660602848706113], [1179, 4278, -0.022984187713549962], [1179, 1089, -0.027626784409920606], [1179, 964, 0.12705751824936229], [1179, 81349, 0.020126477925588551], [1179, 5325, -0.0041183000936273568], [1179, 974, -0.0074685379133837861], [1179, 1105, -0.025120855244532621], [1179, 978, -0.020839254764104583], [1179, 980, -0.012036406746753816], [1179, 996, -0.12762433442648327], [1179, 80352, -0.070305369164112702], [1179, 4452, -0.34445543458478545], [1179, 1010, -0.089271889672878205], [1179, 892, -0.031327468376920783], [924, 34344, 0.017083024200454783], [924, 10524, 0.0028854846778717112], [924, 942, 0.75422261513701838], [924, 37298, 0.6823905498390419], [924, 4278, 0.0015727184828867374], [924, 1089, 0.039315723987057245], [924, 964, 0.81719543654785554], [924, 81349, -0.043554148569424904], [924, 5325, 0.0020480160873640558], [924, 974, 0.0005204545875638106], [924, 1105, -0.024263841039643064], [924, 978, 0.094406907830156706], [924, 980, 0.013416531623322046], [924, 996, 0.99801408647978251], [924, 80352, -0.065021644433117892], [924, 4452, -0.054302675303201355], [924, 1010, 0.99510629966201636], [924, 892, -0.027801580301357619], [34344, 10524, -0.0094954609672688681], [34344, 942, -0.0072708455470704763], [34344, 37298, -0.0037138133276049699], [34344, 4278, 0.0017981420190520138], [34344, 1089, -0.022490537249581301], [34344, 964, 0.0019428349314624227], [34344, 81349, -0.0090835879822938215], [34344, 5325, 0.0013053846168910388], [34344, 974, -0.0006931000828726677], [34344, 1105, 0.17333607652397359], [34344, 978, -0.0081413147825027225], [34344, 980, -0.0093712412686488555], [34344, 996, 0.019854406414890474], [34344, 80352, -0.010792116108348151], [34344, 4452, 0.0026918259547345988], [34344, 1010, 0.018712278879553217], [34344, 892, -0.0036652051625344572], [10524, 942, -0.0375783826036621], [10524, 37298, -0.045188614795573324], [10524, 4278, 0.0061812583210892752], [10524, 1089, 0.041987031608810274], [10524, 964, -0.023487168073273574], [10524, 81349, -0.022689683049063214], [10524, 5325, 0.038758960525044767], [10524, 974, -0.0033223410809135956], [10524, 1105, -0.0063157579359313428], [10524, 978, 0.0017184797894660832], [10524, 980, 0.030188668242595907], [10524, 996, 0.005348972007045023], [10524, 80352, -0.030332150631281782], [10524, 4452, 0.0035950581525625172], [10524, 1010, -0.007075034217421612], [10524, 892, -0.012109830194858229], [942, 37298, 0.94375588287501788], [942, 4278, -0.0055824480496982701], [942, 1089, 0.053122165909422842], [942, 964, 0.90404674848082756], [942, 81349, 0.036679748573820586], [942, 5325, -0.018999932269507198], [942, 974, 0.0013312548927820994], [942, 1105, -0.0064006743266762497], [942, 978, -0.036718382492544707], [942, 980, -0.0084785654694471326], [942, 996, 0.71459910784023706], [942, 80352, 0.070999132094001147], [942, 4452, 0.062139998776855096], [942, 1010, 0.7499156901780577], [942, 892, -0.021372788007710596], [37298, 4278, 0.01354066559195337], [37298, 1089, 0.017119810671059252], [37298, 964, 0.8689749447090469], [37298, 81349, 0.026576999428941248], [37298, 5325, -0.017899214281201965], [37298, 974, -0.0014631242572665938], [37298, 1105, -0.0074534707957047584], [37298, 978, -0.038256246091426249], [37298, 980, 0.0069236005547581893], [37298, 996, 0.64185224604444202], [37298, 80352, 0.19487985433713489], [37298, 4452, 0.070667016049629133], [37298, 1010, 0.68533154158842002], [37298, 892, -0.01840349129788264], [4278, 1089, 0.0032864413686004065], [4278, 964, -0.0029686650585439484], [4278, 81349, 0.0012033542106374526], [4278, 5325, -0.0070759944992923188], [4278, 974, -0.00021948647111738736], [4278, 1105, -0.0032160088544361818], [4278, 978, 0.0062902148377223539], [4278, 980, -0.0046117899290427766], [4278, 996, 0.00044419375780327657], [4278, 80352, 0.010240218119028137], [4278, 4452, -0.022934845526239356], [4278, 1010, -8.1966596317915681e-05], [4278, 892, 0.0047512728440464603], [1089, 964, 0.027700086100436363], [1089, 81349, 0.069201740089163882], [1089, 5325, -0.033378217123218888], [1089, 974, -0.0070053741406869378], [1089, 1105, 0.13426026610517866], [1089, 978, 0.12790451408974995], [1089, 980, 0.60735133816197784], [1089, 996, 0.033946384901087909], [1089, 80352, 0.070499036171105825], [1089, 4452, 0.10183735517367498], [1089, 1010, 0.036646068852101803], [1089, 892, 0.072402567411618726], [964, 81349, 0.0080645781073330324], [964, 5325, -0.0083989211280317173], [964, 974, -0.012743454502367722], [964, 1105, -0.032340264815487144], [964, 978, -0.029470525420919363], [964, 980, -0.018280105219825801], [964, 996, 0.78888877501204369], [964, 80352, 0.0099915730010067122], [964, 4452, -0.017973644401978791], [964, 1010, 0.82178132351512645], [964, 892, -0.035871997406155709], [81349, 5325, -0.0041775610429869514], [81349, 974, 0.0014955563590954648], [81349, 1105, -0.016532799742393724], [81349, 978, -0.02702865195364907], [81349, 980, 0.0631879963462922], [81349, 996, -0.053550582915936347], [81349, 80352, -0.07899105741818109], [81349, 4452, -0.0014042622548829787], [81349, 1010, -0.018461983411846412], [81349, 892, -0.0048054521494181714], [5325, 974, -0.011947983523413572], [5325, 1105, -0.064099631038658803], [5325, 978, 0.0029576343067782684], [5325, 980, -0.0011675266762036073], [5325, 996, 0.0012999124354709118], [5325, 80352, 0.018058562066423832], [5325, 4452, -0.020797880128394366], [5325, 1010, 3.6549585115419839e-05], [5325, 892, 0.0025324029869508899], [974, 1105, 0.018075761239587363], [974, 978, 0.019888809367656919], [974, 980, 0.01084370319970719], [974, 996, 0.00025170107493212123], [974, 80352, -0.013222064546111309], [974, 4452, 0.14071226704582968], [974, 1010, 0.0020696098471413536], [974, 892, -0.0046052453287759596], [1105, 978, 0.42682293626328149], [1105, 980, -0.045312557560631489], [1105, 996, -0.02429299977485307], [1105, 80352, -0.042580532196265938], [1105, 4452, -0.097203328878311748], [1105, 1010, -0.035394263038617459], [1105, 892, -0.14378365076112298], [978, 980, 0.10195809360240832], [978, 996, 0.10238807942031097], [978, 80352, -0.0058826983357774029], [978, 4452, -0.07962616798730153], [978, 1010, 0.097162656153847407], [978, 892, 0.30349517924865249], [980, 996, 0.010996792599579057], [980, 80352, 0.058951966895089615], [980, 4452, 0.041863773973021587], [980, 1010, 0.0089052408585792667], [980, 892, 0.032343724600147374], [996, 80352, -0.071660885947752676], [996, 4452, -0.05829837877538413], [996, 1010, 0.99292427033201647], [996, 892, -0.028453822147270883], [80352, 4452, 0.090140028545502793], [80352, 1010, -0.068433623083749354], [80352, 892, 0.024550447996278955], [4452, 1010, -0.069782123348651748], [4452, 892, 0.0015491316173229755], [1010, 892, -0.024094708360357191]], "document_ID": [[5187, "Skype", "", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Skype"], [5192, "Skype", "", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Skype"], [5188, "Skype", "", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Skype"], [6067, "Document3", "file://", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Microsoft Word"], [6066, "ETHICAL ISSUES AND CHALLENGES IN MY OWN RESEARCH.pdf (page 2 of 2)", "", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Preview"], [6079, "https://www2.warwick.ac.uk/fac/soc/pais/people/richardson/nuffield_council_-_ethics_of_biofuel.pdf", "https://www2.warwick.ac.uk/fac/soc/pais/people/richardson/nuffield_council_-_ethics_of_biofuel.pdf", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Safari"], [6084, "Document3", "file://", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Microsoft Word"], [5194, "Skype", "", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Skype"], [6082, "https://www2.warwick.ac.uk/fac/soc/pais/people/richardson/nuffield_council_-_ethics_of_biofuel.pdf", "https://www2.warwick.ac.uk/fac/soc/pais/people/richardson/nuffield_council_-_ethics_of_biofuel.pdf", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Safari"], [5720, "Facebook", "https://www.facebook.com/lukianw/photos/pcb.10155737996904110/10155737991784110/?type=3&theater", "https://reknowdesktopsurveillance.hiit.fi/uploads/C1MR3058G940/original/1513349785.60169.jpeg", "Safari"]], "people": [[921, "pedram", 0.012996606128907717], [980, "lumin_wei", 0.01132616423017817], [978, "pedram_daee", 0.0098298494193589329], [911, "lumin", 0.0093290628717824578], [1010, "trash", 0.0073270322611523695], [37298, "ruotsalo_tuukka", 0.006968538524255408], [942, "antti_k_salovaara", 0.0065479944342718881], [1031, "salvatore", 0.005691350757152186], [2202, "kumpula", 0.0053869512554927824], [1037, "daee", 0.0045611790097129096]]}';
    renderInitialData(data);
  });
  $( "#send1AfterSkpyeDataButton" ).click(function(){
    socket.emit('send1AfterSkpyeData');
  });
  $( "#send2AfterFBDataButton" ).click(function(){
    socket.emit('send2AfterFBData');
  });
  $( "#send3AfterTuukkaDataButton" ).click(function(){
    socket.emit('send3AfterTuukkaData');
  });
  $( "#startStopTheLab" ).click(function(){
    if($(this).text()==="START"){
        socket.emit('userFeedback',JSON.stringify({'Channel':'START'}))
        $(this).text("STOP");
        $(this).css('background-color', 'red');
    }
    else if($(this).text()==="STOP"){
        socket.emit('userFeedback',JSON.stringify({'Channel':'KILL'}));
        $(this).text("START");
        $(this).css('background-color', 'green');
        location.reload();
    }
                                
    //socket.emit('START');
  });
});
