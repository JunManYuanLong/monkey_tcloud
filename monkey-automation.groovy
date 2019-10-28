node('stf'){
    stage('configurate ENV'){
        packageName = "${PackageName}"
        deviceName = "${DeviceName}"
        runTime = "${RunTime}"
        appDownloadUrl = "${AppDownloadUrl}"
        runMode = "${RunMode}"
        buildBelong = "${BuildBelong}"
        systemDevice = "${SystemDevice}"
        loginRequired = "${LoginRequired}"
        loginUsername = "${LoginUsername}"
        loginPassword = "${LoginPassword}"
        defaultAppActivity = "${DefaultAppActivity}"
        tcloudUrl = "${TcloudUrl}"
        taskId = "${TaskId}"
        monkeyId = "${MonkeyId}"
        installAppRequired = "${InstallAppRequired}"
        print("==================> 参数 <==================")
        print("PackageName : " + packageName + "\n" +
              "DeviceName : " + deviceName + "\n" +
              "RunTime : " + runTime + "\n" +
              "AppDownloadUrl : " + appDownloadUrl + "\n" +
              "RunMode : " + runMode + "\n" +
              "BuildBelong : " + buildBelong + "\n" +
              "SystemDevice : " + systemDevice + "\n" +
              "LoginRequired : " + loginRequired + "\n" +
              "LoginUsername : " + loginUsername + "\n" +
              "LoginPassword : " + loginPassword + "\n" +
              "DefaultAppActivity : " + defaultAppActivity + "\n"+
              "MonkeyId: " + monkeyId + "\n" +
              "TcloudUrl: " + tcloudUrl + "\n" +
              "TaskId: " + taskId + "\n" +
              "InstallAppRequired: "+ installAppRequired)
        print("==================> 参数 <==================")
    }

    stage('checkout code'){
        print('=================> 拉取代码  <=================')
        // 此处要修改 url 和 credit
        checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '', url: 'https://github.com/tsbxmw/monkey_tcloud']]])
        sh 'ls'
        print('=================> 拉取代码  <=================')
    }


    stage('运行测试 - Monkey'){
      print("${InstallAppRequired}")
      if ( "${InstallAppRequired}" == "true" || "${InstallAppRequired}" == true ){
          sh 'python run.py run -dn=' + deviceName + ' -pn=' + packageName + ' -rt=' + runTime + ' -adu="' + appDownloadUrl + '" -daa=' + defaultAppActivity + ' -mid=' + monkeyId + ' -tid=' + taskId + ' -turl=' + tcloudUrl + ' -rm=' + runMode + ' -iar=' + installAppRequired
      }else{
        sh 'python run.py run -dn=' + deviceName + ' -pn=' + packageName + ' -rt=' + runTime + ' -adu="' + appDownloadUrl + '" -daa=' + defaultAppActivity + ' -mid=' + monkeyId + ' -tid=' + taskId + ' -turl=' + tcloudUrl + ' -rm=' + runMode
      }
    }


}