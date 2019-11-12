node('stf'){
    stage('configurate ENV'){
        packageName = "${PackageName}"
        deviceName = "${DeviceName}"
        runTime = "${RunTime}"
        appDownloadUrl = "${AppDownloadUrl}"
        runMode = "${RunMode}"
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
        installAppRequired = installAppRequired=="1"
    }


    stage('checkout code'){
        print('=================> 拉取代码  <=================')
        checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '', url: 'https://github.com/tsbxmw/monkey_tcloud']]])
        sh 'ls'
        print('=================> 拉取代码  <=================')
    }

    stage('运行测试 - Monkey'){
      if (installAppRequired == "true" || installAppRequired == true){
      //这里默认使用 python3 运行脚本，注意修改 python 版本
          sh 'python3 run.py run -dn=' + deviceName + ' -pn=' + packageName + ' -rt=' + runTime + ' -adu="' + appDownloadUrl + '" -daa=' + defaultAppActivity + ' -mid=' + monkeyId + ' -tid=' + taskId + ' -turl=' + tcloudUrl + ' -rm=' + runMode + ' -iar=' + installAppRequired
      }else{
        sh 'python3 run.py run -dn=' + deviceName + ' -pn=' + packageName + ' -rt=' + runTime + ' -adu="' + appDownloadUrl + '" -daa=' + defaultAppActivity + ' -mid=' + monkeyId + ' -tid=' + taskId + ' -turl=' + tcloudUrl + ' -rm=' + runMode
      }
    }


}